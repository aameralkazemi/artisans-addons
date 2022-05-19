#coding: utf-8

import json
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models, tools

from odoo.tools.safe_eval import safe_eval


class business_resource_type(models.Model):
    """
    The model to combine various resources by types, like 'Therapists', 'Cardiologist'. Product might be still different
    within the same type
    """
    _name = "business.resource.type"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _description = "Business Resource Type"

    def _compute_appointment_len(self):
        """
        Compute method for appointment_len & planned_appointment_len

        Extra info:
         * We should not make it stored, since it assumes to calculate dynamic fields, as for 'the last 6 months'. Even
           if split in various methods dependance on stored related field doesn't seem safe
        """
        for rtype in self:
            rtype.appointment_len = self.env["business.appointment"].search_count([
                ("resource_id.resource_type_id", "=", rtype.id)
            ])
            rtype.planned_appointment_len = self.env["business.appointment"].search_count([
                ("resource_id.resource_type_id", "=", rtype.id),
                ("state", "=", "reserved"),
            ])

    @api.depends("resource_ids", "resource_ids.active")
    def _compute_resource_len(self):
        """
        Compute method for resource_len
        """
        for rtype in self:
            rtype.resource_len = len(rtype.resource_ids)

    @api.depends("service_method", "service_ids", "always_service_id")
    def _compute_final_service_ids(self):
        """
        Compute method for final_service_ids
        """
        for rtype in self:
            if rtype.service_method == "single":
                rtype.final_service_ids = [(6, 0, [rtype.always_service_id.id])]
            elif rtype.service_method == "multiple":
                rtype.final_service_ids = [(6, 0, rtype.service_ids.ids)]

    @api.depends("rating_ids.rating", "rating_ids.parent_res_id")
    def _compute_rating_satisfaction(self):
        """
        Compute method for rating_satisfaction

        Methods:
         * _calculate_satisfaction_rate of rating.rating
        """
        for rtype in self:
            rate_final = -1
            if rtype.rating_ids:
                rate = self.env["rating.rating"]._calculate_satisfaction_rate(rtype)
                rate_final = rate[rtype.id]
            rtype.rating_satisfaction = rate_final

    def _inverse_company_id(self):
        """
        Inverse method for company_id
        """
        for rtype in self:
            rtype.resource_ids.write({"company_id": rtype.company_id.id})

    name = fields.Char(string="Name", required=True, translate=True)
    resource_ids = fields.One2many("business.resource", "resource_type_id", string="Resources")
    allowed_from = fields.Integer(string="Reservation should be done in", default=1, required=True)
    allowed_from_uom = fields.Selection(
        [
            ("minutes", "minutes"),
            ("hours", "hours"),
            ("days", "days"),
            ("weeks", "weeks"),
            ("months", "months"),
            ("years", "years"),
        ],
        string="From UoM",
        default="days",
        required=True,
    )
    allowed_to = fields.Integer(string="Reservation should not be done after", default=30, required=True)
    allowed_to_uom = fields.Selection(
        [
            ("hours", "hours"),
            ("days", "days"),
            ("weeks", "weeks"),
            ("months", "months"),
            ("years", "years"),
        ],
        string="To UoM",
        default="days",
        required=True,
    )
    allocation_type = fields.Selection(
        [("automatic", "Automatic"), ("manual", "Manual"),],
        string="Resource Selection",
        help="""* If automatic: users would not have to select resources: Odoo would construct time slots for all 
                  resources of chosen type;
                * If manual: a user would have to choose one or a few resources to observe time slots""",
        default="manual",
        required=True,
    )
    allocation_method = fields.Selection(
        [("by_order", "By Order"), ("by_number", "By Appointments Number"), ("by_workload", "By Workload")],
        string="Resource Allocation Method",
        default="by_workload",
        required=True,
        help="""In case of automatic resource selection or in case of manual selection of a few resources, there might 
        be the situation when the same time slots relate to the same resource.
        This setting defines which resource should be taken:
         * By order: a resource with the highest sequence would be taken. Use drag&drop on resources 
               list view. Thus, the most prioritized resources would have the highest workload.
         * By Appointments Number: a resource with the lowest number of open appointments would be taken
         * By Workload: a resource with the lowest duration of open appointments would be taken
        """,
    )
    service_method = fields.Selection(
        [
            ("multiple", "Service should be selected for resources and for appointment"),
            ("single", "Service is always the same for all resources and appointments"),
        ],
        default="multiple",
        required=True,
    )
    pricing_method = fields.Selection(
        [("per_planned_duration", "Planned Duration"), ("per_unit", "Units")],
        default="per_planned_duration",
        string="Calculate price for",
        help="""Related product sale unit of measure would be used in sales order.
        Make sure that it corresponds with appointments pricing method and duration unit of measure   
        * Per Duration - hours/days would be multiplied to related product price
        * Per Units - the price for single appointment is just a product price""",
        required=True,
    )
    service_ids = fields.Many2many(
        "appointment.product",
        "appointment_product_business_resource_type_rel_table",
        "appointment_product_id",
        "business_resource_type_id",
        string="Available Services",
    )
    final_service_ids = fields.Many2many(
        "appointment.product",
        "appointment_product_business_resource_type_final_rel_table",
        "appointment_product_final_id",
        "business_resource_type_final_id",
        string="Services",
        compute=_compute_final_service_ids,
        store=True,
    )
    always_service_id = fields.Many2one("appointment.product", string="Service")
    appointment_len = fields.Integer(
        string="Number of appointments",
        compute=_compute_appointment_len,
        store=False,
    )
    planned_appointment_len = fields.Integer(
        string="Planned appointments",
        compute=_compute_appointment_len,
        store=False,
    )
    resource_len = fields.Integer(
        string="Number of resources",
        compute=_compute_resource_len,
        store=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.user.company_id,
        required=False,
        inverse=_inverse_company_id,
    )
    color = fields.Integer(string='Color')
    calendar_event_workload = fields.Boolean(
        string="Calendar Events as Busy Time",
        help="If checked, for periods when a responsible user has meetings, appointments would not be possible",
    )
    description = fields.Text(string="Description", translate=True)
    default_alarm_ids = fields.Many2many(
        "appointment.alarm",
        "appointment_alarm_business_resource_type_rel_table",
        "appointment_alarm_rel_id",
        "business_resource_type_id",
        string="Default Alarms",
    )
    rating_option = fields.Boolean(
        "Appointments Customer Rating",
        default=False,
        help="Turn on to send rating request when appointment is marked done",
    )
    rating_mail_template_id = fields.Many2one(
        "mail.template",
        string="Rating Email",
        domain=[("model", "=", "business.appointment")],
        help="If not defined, standard 'Appointments: Rating Template' would be used",
    )
    rating_ids = fields.One2many(
        'rating.rating', 
        'parent_res_id', 
        string='Ratings', 
        domain=lambda self: [('parent_res_model', '=', self._name)],
        auto_join=True
    )
    rating_satisfaction = fields.Integer(
        string="Average Rating",
        compute=_compute_rating_satisfaction,
        store=True, 
        default=-1,
    )
    success_mail_template_id = fields.Many2one(
        "mail.template",
        string="Success Email",
        domain=[("model", "=", "business.appointment")],
        help="If not defined, standard 'Appointments: Success Email Template' would be used",
    )
    active = fields.Boolean(string="Active", default=True,)
    sequence = fields.Integer(string="Sequence")

    _order = "sequence, id"

    _sql_constraints = [
        ('allowed_from_check', 'check (allowed_from>0)', ('Allowed before period should be positive!')),
        ('allowed_to_check', 'check (allowed_to>0)', _('Allowed after period should be positive!')),
    ]

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
        action_id["context"] = {"default_resource_type_id": self.id,}
        return action_id

    def action_open_resources(self):
        """
        The method to open resources (introduced for kanban to pass context)

        Returns:
         * dict

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        action_id = self.sudo().env.ref("business_appointment.business_resource_action").read()[0]
        action_id["context"] = {
            "default_resource_type_id": self.id,
            "search_default_resource_type_id": self.id,
        }
        return action_id
    
    def return_types_and_resources(self):
        """
        The method to return resource types and their resources as hierarchy
        Here we have only 2 levels: (1) resource type, (2) its possible resources

        Methods:
         * _state_selection of business.appointment

        Returns:
         * list of folders dict with keys:
           ** id
           ** text - folder_name
           ** resources (for resource types) - list of ids
           ** services (for resource types and resources) - list of ids
         * list of states (chars)

        Extra info:
         * it is multi (not @api.model) to pass context from js
        """
        resource_types = []
        self = self.with_context(lang=self.env.user.lang)
        all_types = self.search([])
        for res_type in all_types:
            resource_ids = []
            for resource in res_type.resource_ids:            
                service_ids = []
                for service in resource.final_service_ids:
                    service_ids.append({
                        "text": service.name,
                        "id": service.id,
                    })
                resource_ids.append({
                    "text": resource.name,
                    "id": resource.id,
                    "services": service_ids,
                })
            res_service_ids = []
            for service in res_type.final_service_ids:
                res_service_ids.append({
                    "text": service.name,
                    "id": service.id,
                })
            resource_types.append({
                "text": res_type.name,
                "id": res_type.id,
                "resources": resource_ids,
                "services": res_service_ids,
            })
        states = self.env["business.appointment"]._state_selection()
        
        initial_context = self._context.copy()
        ba_calendar_defaults = self.env.user.partner_id.ba_calendar_defaults
        blockedDefaults = ["default_resource_type_id", "default_state", "default_resource_id", "default_service_id",
                           "search_default_resource_id", "search_default_resource_type_id",  "search_default_state",
                           "search_default_service_id"]       
        if ba_calendar_defaults and not [True for block in blockedDefaults if initial_context.get(block)]:
            initial_context.update(json.loads(self.env.user.partner_id.ba_calendar_defaults))
        return {
            "availableResourceTypes": resource_types,
            "availableStates": states,
            "initial_context": initial_context,
        }

    def _return_timeframes(self, start_dt=None, end_dt=None):
        """
        The method to calculate and return restrictions on time frames and if necessary check those to chosen dates

        Args:
         * start_dt - starting datetime to search slots
         * end_dt - ending datetime to search slots

        Methods:
         * _return_restriction_delta

        Returns:
         * datetime, datetime (with timezone)

        Extra info:
         * We use safely user timezone here, since in resource calendar it would be transformed properly
         * Expected singleton
        """
        self.ensure_one()
        now =  fields.Datetime.context_timestamp(self.env.user, fields.Datetime.now())
        res_start = now + self._return_restriction_delta(self.allowed_from_uom, self.allowed_from)
        res_start = (start_dt and start_dt >= res_start) and start_dt or res_start
        res_end = now + self._return_restriction_delta(self.allowed_to_uom, self.allowed_to)
        res_end = (end_dt and end_dt <= res_end) and end_dt or res_end
        return res_start.replace(second=0), res_end

    @api.model
    def _return_restriction_delta(self, uom, value):
        """
        The method to calculate relativedelta based on used uom

        Args:
         * uom - 'minutes', 'hours', 'days', 'weeks', 'months', 'years'
         * value - integer

        Returns:
         * relativedelta
        """
        if uom == "minutes":
            delta = relativedelta(minutes=value)
        elif uom == "hours":
            delta = relativedelta(hours=value)
        elif uom == "days":
            delta = relativedelta(days=value)
        elif uom == "weeks":
            delta = relativedelta(weeks=value)
        elif uom == "months":
            delta = relativedelta(months=value)
        else:
            delta = relativedelta(years=value)
        return delta

    @api.model
    def _return_number_of_appointments(self):
        """
        The method to return maximum number of appointments based on configuration

        Returns:
         * int
        """
        ICPSudo = self.env['ir.config_parameter'].sudo()
        multi_schedule = safe_eval(ICPSudo.get_param('ba_multi_scheduling', default='False'))
        appoitnment_number = 1
        if multi_schedule:
            appoitnment_number = int(ICPSudo.get_param('ba_max_multi_scheduling', default='1'))
            appoitnment_number = appoitnment_number <= 0 and 1 or appoitnment_number
        return appoitnment_number

    def return_ba_resources(self, resource_ids):
        """
        The method to return resources related to this resource type

        Args:
         * resource_ids - list of existing resource ids

        Returns:
         * list of dicts (id, display_name)
        """
        add_resource_ids = self.env["business.resource"].search([
            ("resource_type_id", "in", self.ids), 
            ("id", "not in", resource_ids)
        ])
        result = False
        if add_resource_ids:
            result = add_resource_ids.mapped(lambda res: {"id": res.id, "display_name": res.name_get()[0]})
        return result
