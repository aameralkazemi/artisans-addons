# -*- coding: utf-8 -*-

from odoo import api, fields, models

class appointment_analytic(models.Model):
    """
    Overwrite to add website-specific options
    """
    _inherit = "appointment.analytic"
    
    @api.model
    def _sale_state_selection(self):
        """
        Get possible sale states
        """
        return self.env["sale.order"].sudo()._fields["state"]._description_selection(self.env)
    
    @api.model
    def _invoice_status_selection(self):
        """
        Get possible invoice statuses
        """
        return self.env["sale.order"].sudo()._fields["invoice_status"]._description_selection(self.env)

    order_id = fields.Many2one(
        "sale.order",
        string="Sale Order",
        readonly=True,
    )
    sale_state = fields.Selection(
        _sale_state_selection,
        string="Sale State",
        readonly=True,
    )
    invoice_status = fields.Selection(
        _invoice_status_selection,
        string="Invoice Status",
        readonly=True,
    )
    amount_total = fields.Float(
        string="Sale Total",
        readonly=True,
    )

    def _select_query(self):
        """
        Overwrite to add website
        """
        return super(appointment_analytic, self)._select_query() + """,
                a.order_id,
                s.state as sale_state,
                s.invoice_status as invoice_status,
                sum(s.amount_total / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) as amount_total""" 

    def _join_query(self):
        """
        Overwrite to join sale parameters
        """
        return super(appointment_analytic, self)._join_query() + """
                left join sale_order s on (a.order_id=s.id)"""
        
    def _group_by_query(self):
        """
        Overwrite to add website
        """
        return super(appointment_analytic, self)._group_by_query() + """,
                a.order_id,
                s.state,
                s.invoice_status"""
