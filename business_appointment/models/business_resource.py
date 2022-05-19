#coding: utf-8

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from pytz import all_timezones, timezone

from odoo import api, fields, models, tools

from odoo.addons.base.models.res_partner import _tzs
from odoo.addons.resource.models.resource import datetime_to_string, Intervals, string_to_datetime
from odoo.tools.safe_eval import safe_eval

UTCTZ = timezone("UTC")
MAXINTERVALS_NOTTOSPLITBYMONTHS = 14


def get_possible_timezones_by_offset(tz_offset):
    """
    The method to retrieve a possible timezone by its offset (we return the first found)

    Args:
     * tz_offset - int (offset in minutes)

    Returns:
     * char
    """
    offset_days, offset_seconds = 0, int(tz_offset * 60)
    if offset_seconds < 0:
        offset_days = -1
        offset_seconds += 24 * 60
    desired_delta = timedelta(offset_days, offset_seconds)
    null_delta = timedelta(0, 0)
    result = "UTC"
    for tz_name in all_timezones:
        tz = timezone(tz_name)
        non_dst_offset = getattr(tz, '_transition_info', [[null_delta]])[-1]
        if desired_delta == non_dst_offset[0]:
            result = tz_name
            break
    return result

def localize_day_to_resource_datetime(dt, tz):
    """
    The method to calculate day based on given tz

    Args:
     * dt - naive datetime (expressed as UTC)
     * tz - pytz.timezone object
    """
    dt = fields.Datetime.from_string(dt)
    return tz.localize(dt)


class business_resource(models.Model):
    """
    The model to keep settings of who / what should be occupied. E.g. a doctor, a room, etc.
    """
    _name = "business.resource"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin', 'image.mixin']
    _description = "Business Resource"

    @api.depends("resource_type_id.service_ids")
    def _compute_type_available_service_ids(self):
        """
        Compute method for type_available_service_ids
        """
        for appointment in self:
            service_ids = appointment.resource_type_id.service_ids.ids
            appointment.type_available_service_ids = [(6, 0, service_ids)]

    @api.depends("resource_type_id.service_method", "service_ids", "resource_type_id.always_service_id")
    def _compute_final_service_ids(self):
        """
        Compute method for final_service_ids
        """
        for resource in self:
            if resource.service_method == "single":
                resource.final_service_ids = [(6, 0, [resource.resource_type_id.always_service_id.id])]
            elif resource.service_method == "multiple":
                resource.final_service_ids = [(6, 0, resource.service_ids.ids)]

    @api.depends("appointment_ids.resource_id", "appointment_ids.state")
    def _compute_appointment_len(self):
        """
        Compute method for appointment_len & planned_appointment_len
        """
        for resource in self:
            resource.appointment_len = len(resource.appointment_ids)
            resource.planned_appointment_len = len(resource.appointment_ids.filtered(lambda ap: ap.state == 'reserved'))

    @api.depends("resource_type_id.allocation_method", "appointment_ids.resource_id", "appointment_ids.state", 
                 "appointment_ids.duration", "appointment_ids.datetime_start", "appointment_ids.datetime_end", 
                 "appointment_ids.service_id.duration_uom",)
    def _compute_allocation_factor(self):
        """
        Compute method for allocation_factor
        """
        for resource in self:
            allocation_factor = 0
            allocation_method = resource.resource_type_id.allocation_method
            if allocation_method == "by_order":
                allocation_factor = resource.sequence
            elif allocation_method == "by_number":
                allocation_factor = resource.planned_appointment_len
            elif allocation_method == "by_workload":
                allocation_factor = sum(
                    resource.appointment_ids.filtered(lambda ap: ap.state == 'reserved').mapped("duration")
                )
            resource.allocation_factor = allocation_factor

    @api.depends("rating_ids.rating", "rating_ids.parent_res_id")
    def _compute_rating_satisfaction(self):
        """
        Compute method for rating_satisfaction

        Methods:
         * _calculate_satisfaction_rate of rating.rating
        """
        for resource in self:
            rate_final = -1
            if resource.rating_ids:
                rate = self.env["rating.rating"]._calculate_satisfaction_rate(resource)
                rate_final = rate[resource.id]
            resource.rating_satisfaction = rate_final

    def _inverse_name(self):
        """
        Inverse method for name
        """
        for resource in self:
            resource.resource_id.name = resource.name

    def _inverse_resource_type_id(self):
        """
        Inverse method for resource_type_id
        It is for the case of not manual form onchaneg. For details look at onchange
        """
        for resource in self:
            resource.service_ids = [(6, 0, resource.resource_type_id.service_ids.ids)]
            if resource.resource_type_id.company_id != resource.company_id:
                resource.company_id = resource.resource_type_id.company_id

    @api.onchange("resource_type_id")
    def _onchange_resource_type_id(self):
        """
        Onchange method for resource_type_id
        If it is changed we should replace previous services with new ones, and after that remove excess
        Services of resources are alsways subset of resource types
        """
        for resource in self:
            resource.service_ids = [(6, 0, resource.resource_type_id.service_ids.ids)]
            resource.company_id = resource.resource_type_id.company_id

    name = fields.Char(
        string="Name",
        required=True,
        translate=True,
        inverse=_inverse_name,
    )
    resource_type_id = fields.Many2one(
        "business.resource.type",
        string="Type",
        required=True,
        ondelete="cascade",
        inverse=_inverse_resource_type_id,
    )
    resource_calendar_id = fields.Many2one(required=False,)
    appointment_ids = fields.One2many("business.appointment", "resource_id", string="Appointments")
    service_method = fields.Selection(related="resource_type_id.service_method", store=True, compute_sudo=True)
    service_ids = fields.Many2many(
        "appointment.product",
        "appointment_product_business_resource_rel_table",
        "appointment_product_id",
        "business_resource_id",
        string="Available Services",
    )
    final_service_ids = fields.Many2many(
        "appointment.product",
        "appointment_product_business_resource_rel_final_table",
        "appointment_product_final_id",
        "business_resource_final_id",
        string="Services",
        compute=_compute_final_service_ids,
        store=True,
    )
    type_available_service_ids = fields.Many2many(
        "appointment.product",
        "appointment_product_business_resource_rel_table_available",
        "product_id_available",
        "business_resource_id_available",
        string="Type Services",
        compute=_compute_type_available_service_ids,
        store=True,
    )
    appointment_len = fields.Integer(string="Number of appointments", compute=_compute_appointment_len, store=True)
    planned_appointment_len = fields.Integer(
        string="Planned appointments",
        compute=_compute_appointment_len,
        store=True,
    )
    allocation_factor = fields.Float(
        string="Allocation Factor",
        compute=_compute_allocation_factor,
        compute_sudo=True,
        store=True,
    )
    resource_type = fields.Selection(
        related='resource_id.resource_type',
        index=True,
        store=True,
        readonly=False,
        string='Resource Kind',
        default='material',
        required=True,
    )
    user_id = fields.Many2one(
        'res.users',
        'Responsible',
        related='resource_id.user_id',
        store=True,
        readonly=False,
        tracking=3,
    )
    location = fields.Char(string="Location", translate=True)    
    color = fields.Integer(string='Color')
    description = fields.Text(string="Description", translate=True)
    rating_ids = fields.One2many(
        'rating.rating', 
        'resource_id', 
        string='Ratings', 
        auto_join=True
    )
    rating_satisfaction = fields.Integer(
        string="Average Rating",
        compute=_compute_rating_satisfaction,
        store=True, 
        default=-1,
    )
    active = fields.Boolean(
        'Active',
        related='resource_id.active',
        default=True,
        store=True,
        readonly=False,
    )
    sequence = fields.Integer(string="Sequence")
    sucess_email_partner_ids = fields.Many2many(
        "res.partner",
        "res_partner_business_resource_success_rel_table",
        "res_partner_id",
        "business_resource_id",
        string="Success emails CC",
        help="Success email would be also sent for those partners as a copy of a client success email",
    )

    _order = "sequence, id"

    def action_open_appointments(self):
        """
        The method to open appointments (introduced for kanban to pass context)

        Returns:
         * dict

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        action_id = self.sudo().env.ref("business_appointment.business_appointment_action").read()[0]
        action_id["context"] = {
            "default_resource_id": self.id,
            "default_resource_type_id": self.resource_type_id.id
        }
        return action_id

    def action_construct_time_slots(self, resource_type_id, service_id, duration, date_start, date_end,
                                    active_month=False, tz_info={}, chosen_cores=[]):
        """
        The method to calculate time slots for these resources and params (used in JavaScript)
        IT IS THE CORE METHOD OF THE APP

        Args:
         * resource_type_id - int - ID of business.resource.type
         * date_start - date (js Moment)
         * date_end - date (js Moment)
         * service_id - int - ID of appointment.product
         * duration - float
         * active_month - str (date) or False: which might (if any is chosen)
         * tz_info - dict.
            EITHER (if timezone is manually selected):
             ** targetTz - name of chosen timezone
            OR (if timezone is )
             ** timeZoneOffset - int - difference of time from UTC in browser
             ** timeZoneName - char - name of timezone

        Methods:
         * _find_tz_options
         * _retrieve_resource_intervals
         * _calculate_switcher
         * _split_intervals_to_slots
         * _prepare_js_dict_of_slots

        Returns:
         * dict of
          ** day_slots - list of dicts
            *** day: str
            *** slots: - list of dicts: day_to_sort (datetime.date), day (str), start (str), end (str), resource_ids
                        (list of resources IDS), resource resource_names (char)
          ** not_found - bool - if no available slots
          ** tz_options - list of typles
          ** default_tz - str
          ** no_tz - bool - if timezones should not be selected
          ** unique_months - list of available months (str - the first month day)
          ** active_month - str - which month is active
        """
        resource_type_id = self.env["business.resource.type"].browse(resource_type_id)
        resource_ids = self or resource_type_id.resource_ids
        if len(resource_ids) > 1:
            resource_ids = resource_ids.sorted(key=lambda reso: reso.allocation_factor)
        service_id = self.env["appointment.product"].browse(service_id)
        duration_uom = service_id.duration_uom or "hours"
        if not duration or duration <= 0:
            duration = duration_uom == "hours" and service_id.appointment_duration \
                       or service_id.appointment_duration_days*24 or 1
        resource_ids = resource_ids.filtered(lambda re: service_id.id in re.final_service_ids.ids)
        tz_options, default_tz = self._find_tz_options(tz_info=tz_info)
        target_tz = default_tz and timezone(default_tz) or UTCTZ
        date_start = date_start and target_tz.localize(fields.Datetime.from_string(date_start)) or False
        date_end = date_end and target_tz.localize(fields.Datetime.from_string(date_end)) or False
        date_end = date_end and (date_end + relativedelta(days=1)) or False
        intervals_dict = resource_ids._retrieve_resource_intervals(
            start_dt=date_start, 
            end_dt=date_end,
            extra_service_calendar_id=service_id.sudo().extra_working_calendar_id,
        )
        unique_months, to_remove_intervals, current_month, unique_years = self._calculate_switcher(
            interv_dict=intervals_dict,
            duration=duration,
            default_tz=target_tz,
            active_month=active_month,
        )
        slots = []
        for resource in resource_ids:
            intervals = intervals_dict.get(resource.id)
            if to_remove_intervals:
                intervals -= to_remove_intervals
            slots += resource._split_intervals_to_slots(
                intervals=intervals,
                duration=duration,
                default_tz=target_tz,
                duration_uom=duration_uom,
                start_round=duration_uom=="hours" and int(service_id.start_round_rule*60) \
                        or int(service_id.start_round_rule_days*60),
            )
        day_slots = self._prepare_js_dict_of_slots(slots)
        return {
            "day_slots": day_slots,
            "not_found": not day_slots,
            "tz_options": tz_options,
            "no_tz": not tz_options,
            "default_tz": default_tz,
            "unique_months": unique_months,
            "active_month": current_month,
            "unique_years": unique_years,
            "duration_uom": duration_uom,
            "chosen_cores": self._retrieve_appointment_values(chosen_cores, target_tz),
        }

    def action_open_leaves(self):
        """
        The method to open leaves related to this resource and calendar

        Returns:
         * dict of act_window

        Extra info:
         * We have a function since we can't place 'resource_id' on a form due to related specifics
         * Expected singleton
        """
        self.ensure_one()
        action = self.sudo().env.ref("resource.action_resource_calendar_leave_tree").read()[0]
        action["context"] = {
            'default_resource_id': self.resource_id.id,
            'search_default_resource_id': self.resource_id.id,
        }
        return action

    @api.model
    def _find_tz_options(self, tz_info):
        """
        The method to return timezone option
         1. If receive target_tz we use it
            [It also means that the option of tz is turned on (since selection is shown) --> we do not need to check
            configuration]
         2. Otherwise we just take tz received from js
         3. In case default timezone received from JS is not among pytz timezones (an extreme option)--> get try to get
            any with the same offset
         4. If selection is not assumed at all we pass an empty list and as default tz and company time zone as default

        Args:
         * tz_info - dict.
            EITHER (if timezone is manually selected):
             ** targetTz - name of chosen timezone
            OR (if timezone is )
             ** timeZoneOffset - int - difference of time from UTC in browser
             ** timeZoneName - char - name of timezone

        Methods:
         * get_possible_timezones_by_offset

        Returns:
         * list of timezones, char - timezone
        """
        tz_options = _tzs
        default_tz = tz_info.get("targetTz")
        # 1
        if not default_tz:
            ICPSudo = self.env['ir.config_parameter'].sudo()
            timezone_requried = safe_eval(ICPSudo.get_param('business_appointment_timezone_option', default='False'))
            if timezone_requried:
                # 2
                tz_name = tz_info.get("timeZoneName")
                for tz in tz_options:
                    if tz_name == tz[0]:
                        default_tz = tz_name
                        break
                else:
                    # 3
                    tz_offset = tz_info.get("timeZoneOffset") or 0
                    default_tz = get_possible_timezones_by_offset(tz_offset)
            else:
                # 4
                tz_options = []
                default_tz = self.env.user.sudo().company_id.partner_id.tz or self._context.get("tz")
        return tz_options, default_tz

    def _retrieve_resource_intervals(self, start_dt=None, end_dt=None, extra_service_calendar_id=None):
        """
        The method to calculate intervals for resources
         IMPORTANT NOTE: do not merge intervals by various resources, since it is not logically correct: 13:20-13:30;
         13:25-13:50 would result in a single slot 13:20-13:50

        Args:
         * start_dt - starting datetime to search slots
         * end_dt - ending datetime to search slots
         * extra_service_calendar_id - resource.calendar of service - as an extra restriction

        Methods:
         * _return_timeframes of business.resource.type
         * _ba_work_intervals of resource.calendar
         * _amend_intervals_for_already_occupied

        Returns:
         * dict of int (resource id) and Intervals object
        """
        self = self.sudo()
        res_intervals = {}
        for resource in self:
            res_start, res_end = resource.resource_type_id._return_timeframes(start_dt=start_dt, end_dt=end_dt)
            intervals = resource.resource_calendar_id._ba_work_intervals(
                start_dt=res_start,
                end_dt=res_end,
                resource=resource.resource_id,
                extra_service_calendar_id=extra_service_calendar_id,
            )
            intervals -= resource._amend_intervals_for_already_occupied(start_dt=res_start, end_dt=res_end)
            res_intervals.update({resource.id: intervals})
        return res_intervals

    @api.model
    def _calculate_switcher(self, interv_dict, duration="1.0", default_tz=UTCTZ, active_month=False):
        """
        The method goal is to increase performance of slots calculation by spliting slots into months if a period is too
        big
         1. Get all possible intervals (months) which have enough duration
         2. Get unique months, but only in case there are many shifts (no sense to split '10' shifts on 3 pages)
         3. Get intervals which should not be shown (all times not in this month).

        Args:
         * interv_dict - dict of {resource: Interval objects} (look at resource > resource.py)
         * duration - float
         * default_tz - timezone
         * active_month - str (date) - currently chosen month

        Returns:
         * list of dates or False (if splitting to months is not necessary)
         * Interval Object - intervals which time slots should NOT be shown
         * current_month - str - date
         * unique_years - list of unique years
        """
        all_shifts = []
        # 1
        for key, intervals in interv_dict.items():
            for interval in intervals:
                if (interval[1]-interval[0]).seconds >= duration * 3600:
                    start = interval[0].astimezone(default_tz)
                    all_shifts.append(fields.Date.from_string(start.strftime('%Y-%m-01')))
        unique_months = False
        unique_years = False
        # 2
        if len(all_shifts) >= MAXINTERVALS_NOTTOSPLITBYMONTHS:
            unique_months = sorted(list(set(all_shifts)))
            unique_months = len(unique_months) > 1 and unique_months or False
            if unique_months:
                unique_years = list(set([mo.year for mo in unique_months]))
                unique_years = len(unique_years) > 1 and unique_years or False
        # 3
        to_remove_intervals = False
        current_month = False
        if unique_months:
            current_month = active_month and fields.Date.from_string(active_month) in unique_months \
                            and active_month or unique_months[0]
            month_start = default_tz.localize(fields.Datetime.from_string(current_month))
            to_remove_previous = (datetime.min.replace(tzinfo=default_tz), month_start - relativedelta(seconds=1), self)
            to_remove_further = (month_start + relativedelta(months=1), datetime.max.replace(tzinfo=default_tz), self)
            to_remove_intervals = Intervals([to_remove_previous, to_remove_further])
        return unique_months, to_remove_intervals, current_month, unique_years

    def _split_intervals_to_slots(self, intervals, duration=1.0, default_tz=UTCTZ, duration_uom="hours", 
                                  start_round=False):
        """
        The method to split available intervals by required service duration

        Args:
         * intervals - Interval object
         * duration - float
         * default_tz - timezone
         * duration_uom - char - hours or days
         * start_round - int - how start should be rounded

        Methods:
         * _round_time_by_conf
         * _return_lang_date_format

        Returns:
         * list of dicts: day_to_sort (datetime.date), day (str), start (str), end (str), list of resources IDS,
           resource name, e.g.:
            [
                {
                    "day_to_sort": 22-05-2020,
                    "day": "22-05-2020 Tue",
                    "start": "10:00",
                    "end": "10:30",
                    "resource_ids": [17],
                    "resource_names: "John Brown",
                },
                {
                    "day_to_sort": 24-05-2020,
                    "day": "24-05-2020 Wed",
                    "start": "13:00",
                    "end": "13:30",
                    "resource_ids": [(17, John Brown)],
                    "resource_names: "John Brown",
                }
            ]

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        lang_date_format = self._return_lang_date_format()
        slots = []
        for interval in intervals:
            start = self._round_time_by_conf(interval[0], default_tz=default_tz, duration_uom=duration_uom, 
                                             start_round=start_round)
            end = interval[1]
            end_slot = start + relativedelta(hours=duration)
            while end_slot <= end:
                day_to_sort = start.date()
                day = day_to_sort.strftime(lang_date_format)
                start_title = start.strftime("%H:%M")
                end_title = end_slot.strftime("%H:%M")
                if duration_uom == "days":
                    start_title = "{} {}".format(day, start_title)
                    end_title = "{} {}".format(end_slot.date().strftime(lang_date_format), end_title)
                slot = {
                    "day_to_sort": day_to_sort,
                    "real_start_utc": start.astimezone(UTCTZ),
                    "day": day,
                    "start": start_title,
                    "end": end_title,
                    "resource_ids": [self.id],
                    "resource_names": self.name,
                    "title": "{}{} - {}".format(duration_uom == "hours" and day + " " or "", start_title, end_title)
                }
                slots.append(slot)
                start += relativedelta(hours=duration)
                end_slot += relativedelta(hours=duration)
        return slots

    def _amend_intervals_for_already_occupied(self, start_dt=None, end_dt=None,):
        """
        The method to remove from intervals already occupied slots
         1. Check ready slots
         2. Check temporary reservation
         3. Check calendar events if it is set up in resource type

        Args:
         * start_dt - starting datetime to search slots
         * end_dt - ending datetime to search slots

        Methods:
         * _take_expiration_limits of business.appointment.core
         * localize_day_to_resource_datetime

        Returns:
         * Interval objects (look at resource > resource.py)

        Extra info:
         * we consiously do not restrict slots by required date, since we then would substract intervals, while
           search becomes faster + no tz issues. We rely only upon rough separator, since appointments are possible
           only for the future
         * Expected singleton
        """
        self.ensure_one()
        tz = timezone(self.resource_calendar_id.tz)
        start_dt = start_dt.astimezone(tz)
        end_dt = end_dt.astimezone(tz)
        result = []
        start_compare = datetime_to_string(start_dt)
        end_compare = datetime_to_string(end_dt)
        rough_separator = fields.Datetime.now()-relativedelta(days=1)
        # 1
        busy_slots = self.env["business.appointment"].search([
            ("resource_id", "=", self.id),
            ("state", "in", ["reserved"]),
            ("datetime_start", ">", rough_separator),
        ])
        for slot in busy_slots:
            dt0 = string_to_datetime(slot.datetime_start).astimezone(tz)
            dt1 = string_to_datetime(slot.datetime_end).astimezone(tz)
            result.append((max(start_dt, dt0), min(end_dt, dt1), self.resource_id))
        # 2     
        preresrvation_datetime, schedule_datetime = self.env["business.appointment.core"]._take_expiration_limits()
        temp_busy_slots = self.env["business.appointment.core"].search([
            ("resource_id", "=", self.id),
            ("datetime_start", ">", rough_separator),
            "|",
                "&",
                    ("state", "=", "draft"),
                    ("create_date", ">=", preresrvation_datetime),
                "&",
                    ("state", "=", "need_approval"),
                    ("schedule_datetime", ">=", schedule_datetime),
        ])
        for slot in temp_busy_slots:
            dt0 = string_to_datetime(slot.datetime_start).astimezone(tz)
            dt1 = string_to_datetime(slot.datetime_end).astimezone(tz)
            result.append((max(start_dt, dt0), min(end_dt, dt1), self.resource_id))
        # 3
        calendar_event_workload = self.resource_type_id.calendar_event_workload
        if calendar_event_workload:
            partner_id = self.sudo().user_id.partner_id.id
            event_ids = self.env["calendar.event"].search([
                ("partner_ids", "=", partner_id),
                ("start", ">", rough_separator),
            ])
            for slot in event_ids:
                if slot.allday:
                    dt0 = localize_day_to_resource_datetime(slot.start_date, tz)
                    dt1 = localize_day_to_resource_datetime(slot.stop_date+relativedelta(days=1), tz)
                    result.append((max(start_dt, dt0), min(end_dt, dt1), self.resource_id))
                else:
                    dt0 = string_to_datetime(slot.start).astimezone(tz)
                    dt1 = string_to_datetime(slot.stop).astimezone(tz)
                    result.append((max(start_dt, dt0), min(end_dt, dt1), self.resource_id))
        return Intervals(result)

    @api.model
    def _round_time_by_conf(self, appoin_time, default_tz, duration_uom="hours", start_round=False):
        """
        The method to round time for a required precision based on configs

        Args:
         * appoin_time - datetime.datetime (with resource calendar tz)
         * default_tz - timezone
         * duration_uom - char - hours or days
         * start_round - int - how start should be rounded

        Returns:
         * datetime.datetime

        Extra info:
         * we do not care of seconds, considering that 14:22:57 is fine as 14:22:00
        """
        res_datetime = appoin_time.replace(second=0)
        minutes_to_compare = res_datetime.hour * 60 + res_datetime.minute   
        if duration_uom == "hours":
            start_round = start_round or 1
            division_factor = minutes_to_compare // start_round
            if (minutes_to_compare % start_round) != 0:
                division_factor += 1
            to_add_minutes = division_factor * start_round - minutes_to_compare
            res_datetime += relativedelta(minutes=to_add_minutes)
        else:
            start_round = start_round or 0
            if minutes_to_compare > start_round:
                res_datetime += relativedelta(days=1)
            res_datetime += relativedelta(minutes=start_round-minutes_to_compare) 
        return res_datetime.astimezone(default_tz)

    @api.model
    def _prepare_js_dict_of_slots(self, slots):
        """
        The method to prepare slots in a proper format. The idea is combine slots by day for simplier xml representation

        Args:
         * list of slots dict

        Returns:
         * list of dicts
            *** day: str
            *** slots: - list of dicts: day_to_sort (datetime.date), day (str), start (str), end (str), resource_ids
                        (list of resources IDS), resource resource_names (char)
        """
        day_slots = []
        if slots:
            slots = sorted(slots, key=lambda k: (k['day_to_sort'], k['start']))
            cur_day_res = []
            to_check_day = slots[0].get("day")
            previous_start = False
            for slot in slots:
                if slot.get("day") == to_check_day:
                    if slot.get("start") == previous_start:
                        # 5
                        cur_day_res[-1].update({
                            "resource_ids": cur_day_res[-1].get("resource_ids") + slot.get("resource_ids"),
                            "resource_names": "{}, {}".format(
                                cur_day_res[-1].get("resource_names"), slot.get("resource_names")
                            ),
                        })
                    else:
                        cur_day_res.append(slot)
                else:
                    day_slots.append({"day": to_check_day, "slots": cur_day_res})
                    to_check_day = slot.get("day")
                    cur_day_res = [slot]
                previous_start = slot.get("start")
            else:
                day_slots.append({"day": to_check_day, "slots": cur_day_res})       
        return day_slots

    @api.model
    def _retrieve_appointment_values(self, appointments, default_tz):
        """
        The method to construct chosen appointment values, including adaptation by time zone

        Args:
         * appointments - list of dict - id (int), requestID (int)
         * default_tz - timezone object

        Methods:
         * _return_lang_date_format

        Returns
         * list of dicts: id, requestID, title (str)
        """
        res = []
        lang_date_format = self._return_lang_date_format()
        for core in appointments:
            core_id = self.env["business.appointment.core"].sudo().browse(core.get("requestID"))
            duration_uom = core_id.service_id.duration_uom
            start = core_id.datetime_start.astimezone(default_tz)
            end = core_id.datetime_end.astimezone(default_tz)
            start_title = start.strftime("%H:%M")
            end_title = end.strftime("%H:%M")
            day = start.date().strftime(lang_date_format)
            if duration_uom == "days":
                start_title = "{} {}".format(day, start_title)
                end_title = "{} {}".format(end.date().strftime(lang_date_format), end_title)
            title = "{}: {}{} - {}".format(
                core_id.resource_id.name,
                duration_uom == "hours" and day + " " or "", 
                start_title, 
                end_title
            )
            res.append({
                "id": core.get("id"),
                "requestID": core.get("requestID"),
                "title": title,
            })
        return res and res or False

    @api.model
    def _return_lang_date_format(self):
        """
        The method to return date format for js

        Returns:
         * str
        """
        lang = self._context.get("lang")
        lang_date_format = "%m/%d/%Y"
        if lang:
            record_lang = self.env['res.lang'].search([("code", "=", lang)], limit=1)
            lang_date_format = record_lang.date_format
        return lang_date_format
