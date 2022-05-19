#coding: utf-8

from odoo import fields, models


class business_resource_type(models.Model):
    """
    Overwrite to add a new pricing method for invoicing
    """
    _inherit = "business.resource.type"

    pricing_method = fields.Selection(
    	selection_add=[("per_real_duration", "Tracked Duration")],
    	ondelete={"per_real_duration": "set default"},
    )
