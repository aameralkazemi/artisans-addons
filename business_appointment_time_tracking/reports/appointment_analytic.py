# -*- coding: utf-8 -*-

from odoo import fields, models

class appointment_analytic(models.Model):
    """
    Overwrite to add real duration
    """
    _inherit = "appointment.analytic"
    
    total_real_duration = fields.Float(string="Tracked Duration", readonly=True)

    def _select_query(self):
        """
        Overwrite to add website
        """
        return super(appointment_analytic, self)._select_query() + """,
                a.total_real_duration""" 
