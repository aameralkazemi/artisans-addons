# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.addons.base.models.res_partner import _tzs
from odoo.tools.safe_eval import safe_eval


PARAMS = [
    ("business_appointment_timezone_option", safe_eval, "False"),
    ("ba_multi_scheduling", safe_eval, "False"),
    ("ba_max_multi_scheduling", int, "1"),
    ("ba_approval_type", str, "no"),
    ("ba_max_preresevation_time", float, '0.5'),
    ("ba_max_approval_time", float, '2.0'),
    ("ba_max_approval_trials", int, "5"),
    ("ba_confirmation_retry_period", int, "60"),
    ("ba_confirmation_retry_trials", int, "3"),
    ("ba_auto_sale_order", str, "no"),
    ("ba_extra_products_backend", safe_eval, "False"),
]


class res_config_settings(models.TransientModel):
    """
    The model to keep settings of business appointments
    """
    _inherit = "res.config.settings"

    @api.model
    def _default_tz(self):
        """
        Default method for tz
        """
        return self.env.user.company_id.partner_id.tz or self._context.get("tz")

    @api.onchange("module_business_appointment_website")
    def _onchange_module_business_appointment_website(self):
        """
        Onchange method for module_business_appointment_website
        """
        for conf in self:
            if not conf.module_business_appointment_website:
                conf.ba_approval_type = "no"
                conf.module_business_appointment_custom_fields_website = False
                conf.module_business_appointment_website_sale = False

    @api.onchange("module_business_appointment_sale")
    def _onchange_module_business_appointment_sale(self):
        """
        Onchange method for module_business_appointment_sale
        """
        for conf in self:
            if conf.module_business_appointment_sale:
                conf.group_uom = True
            else:
                conf.ba_auto_sale_order = "no"
                conf.module_business_appointment_website_sale = False

    @api.onchange("module_business_appointment_custom_fields")
    def _onchange_module_business_appointment_custom_fields(self):
        """
        Onchange method for module_business_appointment_website
        """
        for conf in self:
            if not conf.module_business_appointment_custom_fields:
                conf.module_business_appointment_custom_fields_website = False

    @api.onchange("ba_multi_scheduling")
    def _onchange_ba_multi_scheduling(self):
        """
        Onchange method for ba_multi_scheduling
        """
        for conf in self:
            if not conf.ba_multi_scheduling:
                conf.ba_max_multi_scheduling = 1

    module_business_appointment_website = fields.Boolean(string="Appointments in Portal and Website")
    module_business_appointment_custom_fields = fields.Boolean(string="Custom Fields")
    module_business_appointment_custom_fields_website = fields.Boolean("Portal and Website Custom Fields")
    module_business_appointment_sale = fields.Boolean("Link Appointments to Sale Orders")
    module_business_appointment_website_sale = fields.Boolean("Website Sales")    
    module_business_appointment_hr = fields.Boolean(string="Employees as Resources")
    module_business_appointment_time_tracking = fields.Boolean(string="Time Tracking")
    ba_multi_scheduling = fields.Boolean(string="Multi Scheduling")
    ba_max_multi_scheduling = fields.Integer(
        string="Maximum Appointments (Backend)",
        help="""This setting is applied only to backend. 
        For portal and website maximum number, please look at website specific options"""
    )
    ba_approval_type = fields.Selection(
        [("no", "No Confirmation"), ("email", "Email Confirmation"), ("sms", "SMS Confirmation"),],
        string="Website / Portal Confirmation",
        help="If sms is chosen but not available, then email would be used."
    )
    ba_max_approval_time = fields.Float(
        string="Maximum Period for Confirmation (h.)",
        help="After this period, not confirmed appointments would be cancelled"
    )
    ba_max_approval_trials = fields.Integer(
        string="Maximum Number of Attempts to Confirm",
        help="After exceeding this number all steps would be cancelled and should be started from scratch",
    )
    ba_confirmation_retry_period = fields.Integer(
        string="New Confirmation Code Minimum Period (s.)",
        help="Agter this period it would be possible to resend the confirmation code",
    )
    ba_confirmation_retry_trials = fields.Integer(
        string="Maximum Number of Code Refreshing",
        help="After exceeding the button 'Resend Code' would not be shown",
    )
    ba_max_preresevation_time = fields.Float(string="Maximum Period for Pre-Reservation")
    business_appointment_timezone_option = fields.Boolean(string="Different Time Zones")
    appoin_comp_tz = fields.Selection( _tzs, string="Company Timezone", default=_default_tz,)
    ba_auto_sale_order = fields.Selection(
        [
            ("no", "No Auto Creation"),
            ("draft", "Auto Draft Sale Order"),
            ("sent", "Sent Quotation (ready to accept and pay)"),
            ("confirmed", "Auto Confirmed Sale Order"),
        ],
        string="Auto Sale Order",
        help="Define wheter sale order should be auto created / confirmed, when appointment is confirmed",
    )
    ba_extra_products_backend = fields.Boolean("Complementary Products Offer")
    group_business_appointment_rating = fields.Boolean(
        "Use Rating for Appointments", 
        implied_group='business_appointment.group_business_appointment_rating',
    )    

    @api.model
    def get_values(self):
        """
        Overwrite to add new system params
        """
        Config = self.env['ir.config_parameter'].sudo()
        res = super(res_config_settings, self).get_values()
        values = {}
        for field_name, getter, default in PARAMS:
            values[field_name] = getter(str(Config.get_param(field_name, default)))
        res.update(**values)
        return res

    def set_values(self):
        """
        Overwrite to add new system params
        """
        Config = self.env['ir.config_parameter'].sudo()
        super(res_config_settings, self).set_values()
        for field_name, getter, default in PARAMS:
            value = getattr(self, field_name, default)
            Config.set_param(field_name, value)
        company_id = self.env.user.company_id
        company_id.partner_id.tz = self.appoin_comp_tz
