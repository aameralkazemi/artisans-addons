# -*- coding: utf-8 -*-

from odoo import fields, models


class res_config_settings(models.TransientModel):
    """
    The model to keep settings of business appointments related to website_sale
    """
    _inherit = "res.config.settings"

    ba_pricelists_prices = fields.Boolean(related="appointment_website_id.ba_pricelists_prices", readonly=False)
