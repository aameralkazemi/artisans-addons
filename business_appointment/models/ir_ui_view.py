#coding: utf-8

from odoo import fields, models


class ir_ui_view(models.Model):
    """
    Overwrite to add a new view type
    """
    _inherit = 'ir.ui.view'

    type = fields.Selection(selection_add=[('appointment_calendar', 'Appointment Calendar')])
