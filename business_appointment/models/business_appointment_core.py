#coding: utf-8

import json
import logging

from datetime import datetime
from pytz import timezone

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError

from odoo.addons.base.models.res_partner import _tzs, _lang_get

_logger = logging.getLogger(__name__)
BUSYWARNING = _("Sorry, this time slot has been just reserved")


def localize_day_to_resource(dt, tz):
    """
    The method to calculate day based on given tz

    Args:
     * dt - naive datetime (expressed as UTC)
     * tz - char - name of pytz.timezone object
    """
    tz = timezone(tz or "UTC")
    return timezone("UTC").localize(dt).astimezone(tz).date()


class business_appointment_core(models.Model):
    """
    The model to keep reservation for possible time slots (it is used as a blank/temporary appointment)
    """
    _name = "business.appointment.core"
    _inherit = ['appointment.contact.info', 'mail.thread', 'mail.activity.mixin']
    _description = "Pre-Reservation"
    _rec_name = "user_id"

    @api.model
    def _state_selection(self):
        """
        The method to construct possible selection values

        Returns:
         * list of typles
        """
        states = [
            ("draft", _("Pre-Reservation")),
            ("need_approval", _("Awaiting Confirmation")),
            ("processed", _("Processed")),
        ]
        return states

    @api.depends("datetime_start", "datetime_end", "service_id.duration_uom")
    def _compute_duration(self):
        """
        Compute method for duration, report_duration_hours, report_duration_days
        """
        for appointment in self:
            duration = (appointment.datetime_end - appointment.datetime_start).total_seconds() / 3600
            appointment.report_duration_hours = duration
            duration_days = duration / 24
            appointment.report_duration_days = duration_days
            if appointment.service_id.duration_uom == "days":
                duration = duration_days
            appointment.duration = duration

    @api.depends('datetime_start', 'resource_id')
    def _compute_day_date(self):
        """
        Compute method for day_date, day_month, day_year (! in resource timezone !)
        Required for proper xml filters

        Methods:
         * localize_day_to_resource
        """
        for appointment in self:
            target_tz = appointment.sudo().resource_id.resource_calendar_id.tz
            resource_day_date = localize_day_to_resource(appointment.datetime_start, target_tz)
            appointment.day_date = resource_day_date
            appointment.day_month = datetime.strftime(resource_day_date, '%m-%Y')
            appointment.day_year = datetime.strftime(resource_day_date, '%Y')

    def _compute_late_to_know(self):
        """
        Compute method for late_to_know
        """
        now = fields.Datetime.now()
        for appointment in self:
            if appointment.datetime_start < now and appointment.state in ["draft", "need_approval", "reserved"]:
                appointment.late_to_know = True
            else:
                appointment.late_to_know = False

    state = fields.Selection(
        _state_selection,
        string="Stage",
        default="draft",
        help="""Pre-Reservation - customer is not yet defined, but time is already reserved
        Awaiting Confirmation - in case of need for customer email/phone cnfirmation or internal approval
        Processed - appointment is planned or cancelled because of time expiration""",
        tracking=2,
    )
    resource_id = fields.Many2one(
        "business.resource",
        string="Resource",
        required=True,
        tracking=3,
    )
    user_id = fields.Many2one(related="resource_id.user_id", compute_sudo=True, store=True,)
    partner_id = fields.Many2one(tracking=4,)
    company_id = fields.Many2one(related="resource_id.company_id", compute_sudo=True, store=True,)
    resource_type_id = fields.Many2one(related="resource_id.resource_type_id", compute_sudo=True, store=True,)
    service_id = fields.Many2one(
        "appointment.product",
        string="Service",
        required=True,
        tracking=5,
    )
    duration = fields.Float(
        string="Duration",
        compute=_compute_duration,
        compute_sudo=True,
        store=True,
    )
    report_duration_hours = fields.Float(
        string="Planned Duration (hours)",
        compute=_compute_duration,
        compute_sudo=True,
        store=True,
    )
    report_duration_days = fields.Float(
        string="Planned Duration (days)",
        compute=_compute_duration,
        compute_sudo=True,
        store=True,
    )
    datetime_start = fields.Datetime(string="Reserved Time", required=True, tracking=1)
    datetime_end = fields.Datetime(string="Reserved Time End", required=True, tracking=1)
    schedule_datetime = fields.Datetime(string="Schedule Datetime", default=lambda self: fields.Datetime.now())
    day_date = fields.Date(string="Day", compute=_compute_day_date, store=True)
    day_month = fields.Char(string="Month", compute=_compute_day_date, store=True)
    day_year = fields.Char(string="Year", compute=_compute_day_date, store=True)
    late_to_know = fields.Boolean(string="Late but yet Planned", compute=_compute_late_to_know)
    tz = fields.Selection(_tzs, string="Timezone",)
    lang = fields.Selection(_lang_get,  string='Language', default=lambda self: self.env.lang)
    reservation_group_id = fields.Many2one("appointment.group", string="Appointment Group",)
    extra_product_ids = fields.One2many(
        "associated.product.line",
        "appointment_core_id",
        string="Complementary Products",
    )

    _order = "datetime_start desc, id"

    @api.model
    def create(self, vals):
        """
        Overwrite to check whether the time slot is not yet occupied

        Methods:
         * _prepare_prereservation_specific_vals
         * _check_busy_now_prereserv - to make sure we do not create slot which is already occupied
        """
        vals = self._prepare_prereservation_specific_vals(vals)
        res = super(business_appointment_core, self).create(vals)
        res._check_busy_now_prereserv()
        return res

    @api.model
    def create_reservation(self, core_vals):
        """
        The wrapper method to create in order to calculate proper resource from the list.
        2 goals are:
         * to order resources according to the sequence defined in the resource type
         * to check busy one by one in order to avoid the case when one of possible resources is reserver in meantime
        
        Args:
         * dict to creatr business.appointment core (the only different is 'resource_ids_list' instead of 'resource_id')

        Returns:
         * int - id - of created core object
        """
        res = False
        if core_vals.get("resource_ids_list"):
            resources = [int(item) for item in core_vals.get("resource_ids_list")]
            resources = self.env["business.resource"].browse(resources)
            core_vals.pop("resource_ids_list")
            if len(resources) > 1:
                resources = resources.sorted(key=lambda reso: reso.allocation_factor)
            for resource in resources:
                try:
                    final_vals = core_vals.copy()
                    final_vals.update({"resource_id": resource.id,})
                    res = self.create(final_vals).id
                    break
                except Exception as e:
                    _logger.warning("Time slot is not reserved: {}. Trying another resource".format(e))
                    res = False
        if not res:
            raise UserError(BUSYWARNING)
        return res

    @api.model
    def _prepare_prereservation_specific_vals(self, vals):
        """
        The helper method to process values specific for pre-reservations

        Args:
         * vals - dict

        Methods:
         * _find_tz_options of business.resource

        Returns:
         * vals - dict

        Extra info:
         * As reservation_group_id we receive here the previous (very first pre-reservation)
        """
        if self._name == "business.appointment.core":
            if vals.get("reservation_group_id"):
                reservation_group_id = self.browse(vals.get("reservation_group_id")).reservation_group_id   
                if not reservation_group_id:
                    reservation_group_id = self.env["appointment.group"].create({})
                vals.update({"reservation_group_id": reservation_group_id.id})
            else:
                reservation_group_id = self.env["appointment.group"].create({})
                vals.update({"reservation_group_id": reservation_group_id.id})
            if vals.get("tz"):
                x1, default_tz = self.env["business.resource"].sudo()._find_tz_options(vals.get("tz"))
                vals.update({"tz": default_tz})
            if self._context.get("lang"):
                vals.update({"lang": self._context.get("lang")})
        return vals

    def name_get(self):
        """
        Overloading the method to make a name, since it doesn't have own
        """
        result = []
        for appointment in self:
            name = _(u"Appointment for {} by {}".format(
                appointment.resource_id.sudo().name,
                appointment.partner_id.sudo().name or appointment.sudo().contact_name,
            ))
            result.append((appointment.id, name))
        return result

    @api.model
    def action_clean_expired_prereserv(self):
        """
        Method to clean expired pre-reservied and non-confirmed appointments
        We also remove processed time slots if exists to speed up search

        Methods:
         * _check_expired
        """
        to_remove_appointments = self._check_expired()
        to_remove_appointments.unlink()
        to_remove_groups = self.env["appointment.group"].search([
            "|",
                ("appointment_len", "=", 0),
                ("appointment_ids", "=", False),
        ])
        to_remove_groups.unlink()

    def action_cancel_prereserv(self):
        """
        The method to change state to processed
        """
        for appointment in self:
            appointment.state = "processed"

    def action_start_prereserv(self):
        """
        The method to change state to need approval

        Returns:
         * business.appointment.core recordset
        """
        for appointment in self:
            if not appointment.partner_id and not appointment.contact_name:
                raise UserError(_("Either contact or contact name should be defined!"))
            appointment.state = "need_approval"
            appointment.schedule_datetime = fields.Datetime.now()
        return self

    def action_confirm_prereserv(self):
        """
        The method to change state to processed

        Methods:
         * _confirm_prereserv
        """
        appointments = self._confirm_prereserv()
        return appointments

    def _confirm_prereserv(self, existing_appointment_ids=False):
        """
        The method to change state to processed

        Args:
         * existing_appointment_ids - optional if we should write in existing appointments

        Methods:
         * _prepare_vals_for_real_appointment_prereserv
         * _send_success_email of business.appointment

        Returns:
         * business.appointment recordset

        Extra info:
         * we do not check for uniqueness since it would be checked when appointment is created. Because of this,
           we firstly move an appointment and only then create a real appointment
        """
        if self.env.user._is_public():
            self = self.with_user(SUPERUSER_ID)
        now = fields.Datetime.now()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        approval_type = str(ICPSudo.get_param('ba_approval_type', default='no'))
        confirmation = 10000 # just big number of hours
        if approval_type != "no":
            confirmation = float(ICPSudo.get_param('ba_max_approval_time', default='2.0'))
        schedule_datetime = now - relativedelta(hours=confirmation)
        appointment_ids = existing_appointment_ids or self.env["business.appointment"]
        for appointment in self:
            if appointment.state == "need_approval":
                if appointment.schedule_datetime < schedule_datetime:
                    raise UserError(_("Sorry, this appointment might not be confirmed due to its expiration"))
                appointment.state = "processed"
                vals = appointment._prepare_vals_for_real_appointment_prereserv()
                if existing_appointment_ids:
                    existing_appointment_ids.extra_product_ids = False # to remove outdated extras
                    existing_appointment_ids.write(vals)
                else:
                    new_appointment = self.env["business.appointment"].create(vals)
                    appointment_ids += new_appointment
        reshedule = existing_appointment_ids and True or False
        appointment_ids._send_success_email(reshedule=reshedule)
        return appointment_ids

    @api.model
    def _check_expired(self, checked_ids=False):
        """
        Method to check draft preservations for being expired

        Args:
         * checked_ids - list of checked ids (otherwise all cores are checked)

        Methods:
         * _take_expiration_limits

        Returns
         * business.appointment.core recordset (filtered for expired)
        """
        preresrvation_datetime, schedule_datetime = self._take_expiration_limits()
        domain = checked_ids and [("id", "in", checked_ids)] or []
        domain += [
            "|",  "|",
                "&",
                    ("state", "=", "draft"),
                    ("create_date", "<", preresrvation_datetime),
                "&",
                    ("state", "=", "need_approval"),
                    ("schedule_datetime", "<", schedule_datetime),
                ("state", "=", "processed"),
        ]
        res = self.search(domain)
        return res

    @api.model
    def _take_expiration_limits(self):
        """
        The method helper to retrieve preservation time limits

        Returns:
         * dattetime, datetime
        """
        now = fields.Datetime.now()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        preresrvation = float(ICPSudo.get_param('ba_max_preresevation_time', default='0.5'))
        approval_type = str(ICPSudo.get_param('ba_approval_type', default='no'))
        confirmation = 100000 # just big number
        if approval_type != 'no':
            confirmation = float(ICPSudo.get_param('ba_max_approval_time', default='2.0'))
        preresrvation_datetime = now - relativedelta(hours=preresrvation)
        schedule_datetime = now - relativedelta(hours=confirmation)
        return preresrvation_datetime, schedule_datetime

    def _prepare_vals_for_real_appointment_prereserv(self):
        """
        The method to prepare vals for real appointment based on pre-reservation

        Methods:
         * _check_existing_duplicates
         * _return_partner_values of appointment.contact.info
         * _find_tz_options

        Return:
         * dict of vals for business.appointment

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        partner_id = self.partner_id or self.reservation_group_id.partner_id
        if not partner_id:
            if not self.contact_name:
                raise UserError(_("Either contact or contact name should be defined!"))
            exist_partner_id = self._check_existing_duplicates(self.email, self.mobile, self.phone)
            if exist_partner_id:
                raise UserError(
                    _("Partner with the same email, mobile or phone already exists: {} ({})".format(
                        exist_partner_id.sudo().name, 
                        exist_partner_id.sudo().id
                    ))
                )             
            partner_vals = self._return_partner_values(True)         
            if self.tz:
                partner_vals.update({"tz": self.tz})
            if self.lang:
                partner_vals.update({"lang": self.lang})
            partner_company_id = self.parent_company_id
            if not partner_company_id and self.partner_name:
                partner_company_id = self.env["res.partner"].sudo().create({
                    "name": self.partner_name,
                    'is_company': True,
                })
            partner_vals.update({
                'parent_id': partner_company_id and partner_company_id.id or False,
                'is_company': False,            
            })
            partner_id = self.env["res.partner"].sudo().create(partner_vals)
            self.partner_id = partner_id
            self.reservation_group_id.partner_id = partner_id
        extra_product_ids = []
        for extra in self.extra_product_ids:
            extra_product_ids.append([0, 0, {
                "product_id": extra.product_id.id,
                "product_uom_qty": extra.product_uom_qty,
            }])
        extra_product_ids = extra_product_ids or False
        vals = {
            "description": self.description,
            "resource_id": self.resource_id.id,
            "service_id": self.service_id.id,
            "datetime_start": self.datetime_start,
            "datetime_end": self.datetime_end,
            "schedule_datetime": self.schedule_datetime,
            "start_slot_datetime": self.create_date,
            "partner_id": partner_id.id,
            "pricelist_id": self.pricelist_id.id,
            "alarm_ids": [(6, 0, self.resource_id.resource_type_id.default_alarm_ids.ids)],
            "extra_product_ids": extra_product_ids,
        }
        return vals

    def _check_busy_now_prereserv(self):
        """
        This method is to make 100 sure that no appointments or pre-reservation is done for this slot, e.g. in case
        when slots are generated for 2 users, and both click on the same. Or for the case when appointment is created
        manually.
        1. Check actual appointments
        2. Check preservations
           We check only regural appointments and draft preservations, since for confirmed pre-reservations we consider
           FIFO. And it is hardly possible situation
        3. Check calendar events if asked to
           We calculate day of slot in resource time zone to make sure all-day events are crossing (which are in
           resource user timezone)
        4. This is done since website try/except does not trigger traceback    

        Methods:
         * localize_day_to_resource

        Extra info:
         * We do not check work time due to enormous complexite of such checks - it would take too much time
         * Expected singleton
        """
        self = self.sudo()
        self.ensure_one()
        error = False
        domain = [
            ("resource_id", "=", self.resource_id.id),
            "|",
                "&",
                    ("datetime_start", ">=", self.datetime_start),
                    ("datetime_start", "<", self.datetime_end),
                "&",
                    ("datetime_end", ">", self.datetime_start),
                    ("datetime_end", "<=", self.datetime_end),
        ]
        # 1
        domain_real = [("state", "in", ("reserved",))] + domain
        if self._name == "business.appointment":
            domain_real = [("id", "!=", self.id)] + domain_real
        busy_slot = self.env["business.appointment"].search(domain_real, limit=1)
        if busy_slot:
            error = True
        elif self._name == "business.appointment" or self.state == "draft":
            # 2
            now = fields.Datetime.now()
            ICPSudo = self.env['ir.config_parameter'].sudo()
            preresrvation = float(ICPSudo.get_param('ba_max_preresevation_time', default='0.5'))
            confirmation = float(ICPSudo.get_param('ba_max_approval_time', default='2.0'))
            preresrvation_datetime = now - relativedelta(hours=preresrvation)
            schedule_datetime = now - relativedelta(hours=confirmation)
            domain_preserved = [
                "|",
                    "&",
                        ("state", "=", "draft"),
                        ("create_date", ">=", preresrvation_datetime),
                    "&",
                        ("state", "=", "need_approval"),
                        ("schedule_datetime", ">=", schedule_datetime)
                ] + domain
            if self._name == "business.appointment.core":
                domain_preserved = [("id", "!=", self.id)] + domain_preserved
            temp_busy_slot = self.env["business.appointment.core"].search(domain_preserved, limit=1)
            if temp_busy_slot:
                error = True
        # 3
        if self.resource_type_id.calendar_event_workload and not error:
            tz = self.sudo().resource_id.resource_calendar_id.tz
            start_day_date = localize_day_to_resource(self.datetime_start, tz)
            stop_day_date = localize_day_to_resource(self.datetime_end, tz)
            partner_id = self.user_id.partner_id.id
            event_ids = self.env["calendar.event"].search([
                ("partner_ids", "=", partner_id),
                "|",
                    "&",
                        ("allday", "=", True),
                        "|",
                            '&',
                                ("start_date", ">=", start_day_date),
                                ("start_date", "<=", stop_day_date),
                            '&',
                                ("stop_date", ">=", start_day_date),
                                ("stop_date", "<=", stop_day_date),
                    "&",
                        ("allday", "=", False),
                        "|",
                            '&',
                                ("start", ">=", self.datetime_start),
                                ("start", "<", self.datetime_end),
                            '&',
                                ("stop", ">", self.datetime_start),
                                ("stop", "<=", self.datetime_end),
            ], limit=1)
            if event_ids:
                error = True
        if error:
            if self._name == "business.appointment.core":
                self.state = "processed"
            raise UserError(BUSYWARNING)
