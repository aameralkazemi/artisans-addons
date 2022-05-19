#coding: utf-8

import logging

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class website(models.Model):
    """
    Overwrite to keep configuration for time slots
    """
    _inherit = "website"
    _all_contact_fields = ['phone', 'mobile', 'street', 'street2', 'zipcode', 'city', 'state_id', 'country_id', 
                           'function', 'title']

    def _inverse_ba_turn_on_appointments(self):
        """
        Inverse method for ba_turn_on_appointments
        """
        for record in self:
            if not record.ba_turn_on_appointments:
                record.ba_turn_on_appointments_public = False

    def _inverse_ba_turn_on_appointments_public(self):
        """
        Inverse method for ba_turn_on_appointments_public (to create menu)
        """
        for record in self:
            exist_ids = self.env["website.menu"].search([
                ("url", "=", "/appointments"), 
                ('website_id', '=', record.id),
            ])
            if record.ba_turn_on_appointments_public:
                if not exist_ids:                  
                    try:
                        values = {
                            "name": _("Appointments"),
                            "url": "/appointments",
                            "parent_id": record.menu_id.id,
                            "website_id": record.id,
                            "sequence": 60,
                        }
                        new_menu_id = self.env["website.menu"].create(values)
                    except Exception as e:
                        _logger.warning(e)
            else:
                exist_ids.unlink()

    ba_turn_on_appointments = fields.Boolean(
        string="Business appointments in portal",
        default=True,
        inverse=_inverse_ba_turn_on_appointments,
    )
    ba_turn_on_appointments_public = fields.Boolean(
        string="Business appointments on website",
        default=False,
        inverse=_inverse_ba_turn_on_appointments_public,
    )
    ba_max_multi_scheduling_portal = fields.Integer(
        string="Maximum Appointments (Portal)",
        default=1,
        help="Define how many time slots might be selected during scheduling",
    )
    ba_agree_to_terms_and_conditions = fields.Boolean(string="Agree on terms and conditions")
    ba_rtypes_portal_filters_ids = fields.Many2many(
        "ir.filters",
        "ir_filters_website_ba_rtype_rel_table",
        "ir_filters_id",
        "website_id",
        string="Custom Portal Resource Types Filters",
    )
    ba_rtypes_portal_search_ids = fields.Many2many(
        "business.appointment.custom.search",
        "ba_custom_search_website_rtype_rel_table",
        "knowsystem_custom_search_id",
        "website_id",
        string="Custom Portal Resource Types Search",
    )
    show_ba_rtypes_full_details = fields.Boolean(string="Show types full details pages",)
    ba_resources_portal_filters_ids = fields.Many2many(
        "ir.filters",
        "ir_filters_website_resource_rel_table",
        "ir_filters_id",
        "website_id",
        string="Custom Portal Resource Filters",
    )
    ba_resources_portal_search_ids = fields.Many2many(
        "business.appointment.custom.search",
        "ba_custom_search_website_resource_rel_table",
        "knowsystem_custom_search_id",
        "website_id",
        string="Custom Portal Resource Search",
    )
    show_ba_resource_full_details = fields.Boolean(string="Show resources full details pages",)
    ba_services_portal_filters_ids = fields.Many2many(
        "ir.filters",
        "ir_filters_website_service_rel_table",
        "ir_filters_id",
        "website_id",
        string="Custom Portal Service Filters",
    )
    ba_service_portal_search_ids = fields.Many2many(
        "business.appointment.custom.search",
        "ba_custom_search_website_service_rel_table",
        "knowsystem_custom_search_id",
        "website_id",
        string="Custom Portal Service Search",
    )
    ba_portal_appointments_filters_ids = fields.Many2many(
        "ir.filters",
        "ir_filters_portal_appintment_rel_table",
        "ir_filters_id",
        "website_id",
        string="Custom Portal Appointment Filters",
    )
    ba_portal_appointments_search_ids = fields.Many2many(
        "business.appointment.custom.search",
        "ba_custom_search_website_portal_appoinment_rel_table",
        "knowsystem_custom_search_id",
        "website_id",
        string="Custom Portal Appointment Search",
    )
    show_ba_services_full_details = fields.Boolean(string="Show services full details pages",)
    ba_step1 = fields.Char(
        "Label for step 1: Choose resource type",
        default="Choose resource type",
        translate=True,
        required=True,
    )
    ba_step2 = fields.Char(
        "Label for step 2: Choose resource",
        default="Choose resource",
        translate=True,
        required=True,
    )
    ba_step3 = fields.Char(
        "Label for step 3: Choose service",
        default="Choose service",
        translate=True,
        required=True,
    )
    ba_step4 = fields.Char(
        "Label for step 4: Chose time",
        default="Chose time",
        translate=True,
        required=True,
    )
    ba_step5 = fields.Char(
        "Label for step 5: Account Details",
        default="Account Details",
        translate=True,
        required=True,
    )
    ba_step6 = fields.Char(
        "Label for step 6: Confirmation",
        default="Confirmation",
        translate=True,
        required=True,
    )
    ba_contact_info_mandatory_ids = fields.Many2many(
        "ir.model.fields",
        "ir_model_fields_website_mandatory_rel_table",
        "ir_model_fields_id",
        "website_id",
        string="Mandatory Account Details",
        domain=lambda self: [
            ('model_id', '=', 'appointment.contact.info'), 
            ('name', 'in', self._all_contact_fields)
        ]
    )
    ba_contact_info_optional_ids = fields.Many2many(
        "ir.model.fields",
        "ir_model_fields_website_optional_rel_table",
        "ir_model_fields_id",
        "website_id",
        string="Optional Account Details",
        domain=lambda self: [
            ('model_id', '=', 'appointment.contact.info'), 
            ('name', 'in', self._all_contact_fields)
        ]
    )
    ba_agree_to_terms_and_conditions = fields.Boolean(string="Agree on terms and conditions",)
    ba_agree_to_terms_public_only = fields.Boolean(string="Terms for public users only", default=True)
    ba_agree_to_terms_text = fields.Text(
        string="Agree on terms text",
        default="I have read and agree to the terms presented in the <a href='/''>Terms and Conditions agreement</a>.",
        translate=True,
    )
    ba_extra_products_frontend = fields.Boolean("Complementary Products for Reservation")   

    def _return_website_ba_contact_fields(self):
        """
        The method to return which fields are required / might be filled during reservation

        Returns:
         * list of char - all field names
         * list of char - only mandatory field names

        Extra info:
         * "contact_name", "email" are always required fields disregarding settings
         * Expected singleton
        """
        self.ensure_one()
        self = self.sudo()
        mandatory_ids = self.ba_contact_info_mandatory_ids.mapped("name") + ["contact_name", "email"]
        optional_ids = self.ba_contact_info_optional_ids.mapped("name")
        return optional_ids + mandatory_ids, mandatory_ids
