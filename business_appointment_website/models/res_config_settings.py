# -*- coding: utf-8 -*-

from odoo import fields, models


class res_config_settings(models.TransientModel):
    """
    The model to keep settings of business appointments on website
    """
    _inherit = "res.config.settings"

    def _default_appointment_website_id(self):
        """
        Default method for appointment_website_id
        """
        return self.env['website'].search([('company_id', '=', self.env.company.id)], limit=1)

    def _onchange_ba_multi_scheduling(self):
        """
        Re-write to update portal param
        """
        super(res_config_settings, self)._onchange_ba_multi_scheduling()
        for conf in self:
            if not conf.ba_multi_scheduling:
                conf.ba_max_multi_scheduling_portal = 1            

    appointment_website_id = fields.Many2one(
        "website",
        string='Website for appointments',
        default=_default_appointment_website_id, 
        ondelete='cascade',
    )
    ba_turn_on_appointments = fields.Boolean(related="appointment_website_id.ba_turn_on_appointments", readonly=False)
    ba_turn_on_appointments_public = fields.Boolean(
        related="appointment_website_id.ba_turn_on_appointments_public",
        readonly=False,
    )
    ba_max_multi_scheduling_portal = fields.Integer(
        related="appointment_website_id.ba_max_multi_scheduling_portal",
        readonly=False,
    )
    ba_rtypes_portal_filters_ids = fields.Many2many(
        related="appointment_website_id.ba_rtypes_portal_filters_ids",
        readonly=False,
    )
    ba_rtypes_portal_search_ids = fields.Many2many(
        related="appointment_website_id.ba_rtypes_portal_search_ids",
        readonly=False,
    )
    show_ba_rtypes_full_details = fields.Boolean(
        related="appointment_website_id.show_ba_rtypes_full_details",
        readonly=False,
    )
    ba_resources_portal_filters_ids = fields.Many2many(
        related="appointment_website_id.ba_resources_portal_filters_ids",
        readonly=False,
    )
    ba_resources_portal_search_ids = fields.Many2many(
        related="appointment_website_id.ba_resources_portal_search_ids",
        readonly=False,
    )
    show_ba_resource_full_details = fields.Boolean( 
        related="appointment_website_id.show_ba_resource_full_details",
        readonly=False,    
    )
    ba_services_portal_filters_ids = fields.Many2many(
        related="appointment_website_id.ba_services_portal_filters_ids",
        readonly=False,
    )
    ba_service_portal_search_ids = fields.Many2many(
        related="appointment_website_id.ba_service_portal_search_ids",
        readonly=False,
    )
    ba_portal_appointments_filters_ids = fields.Many2many(
        related="appointment_website_id.ba_portal_appointments_filters_ids",
        readonly=False,
    )
    ba_portal_appointments_search_ids = fields.Many2many(
        related="appointment_website_id.ba_portal_appointments_search_ids",
        readonly=False,
    )
    show_ba_services_full_details = fields.Boolean( 
        related="appointment_website_id.show_ba_services_full_details",
        readonly=False,
    )
    ba_step1 = fields.Char(related="appointment_website_id.ba_step1", readonly=False)
    ba_step2 = fields.Char(related="appointment_website_id.ba_step2", readonly=False)
    ba_step3 = fields.Char(related="appointment_website_id.ba_step3", readonly=False)
    ba_step4 = fields.Char(related="appointment_website_id.ba_step4", readonly=False)
    ba_step5 = fields.Char(related="appointment_website_id.ba_step5", readonly=False)
    ba_step6 = fields.Char(related="appointment_website_id.ba_step6", readonly=False)
    ba_contact_info_mandatory_ids = fields.Many2many(
        related="appointment_website_id.ba_contact_info_mandatory_ids",
        readonly=False,
    )
    ba_contact_info_optional_ids = fields.Many2many(
        related="appointment_website_id.ba_contact_info_optional_ids",
        readonly=False,
    )
    ba_agree_to_terms_and_conditions = fields.Boolean(
        related="appointment_website_id.ba_agree_to_terms_and_conditions",
        readonly=False,
    )
    ba_agree_to_terms_public_only = fields.Boolean(
        related="appointment_website_id.ba_agree_to_terms_public_only",
        readonly=False,
    )
    ba_agree_to_terms_text = fields.Text(
        related="appointment_website_id.ba_agree_to_terms_text",
        readonly=False,        
    )
    ba_extra_products_frontend = fields.Boolean(
        related="appointment_website_id.ba_extra_products_frontend",
        readonly=False,        
    )

    def set_values(self):
        super(res_config_settings, self).set_values()
