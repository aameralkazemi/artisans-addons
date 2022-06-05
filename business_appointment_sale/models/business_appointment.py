#coding: utf-8

from odoo import api, fields, models


class business_appointment(models.Model):
    """
    Overwrite to add a new pricing method for invoicing
    """
    _inherit = "business.appointment"

    @api.depends("order_id.state")
    def _compute_sale_state(self):
        """
        Compute method for sale_state
        """
        for appointment in self:
            appointment.sale_state = appointment.order_id and appointment.order_id.state or False

    order_id = fields.Many2one("sale.order", string="Sale Order")
    sale_state = fields.Char(
        string="Sale State",
        compute=_compute_sale_state,
        store=True,
        compute_sudo=True,
        translate=False,
    )

    @api.model
    def create(self, values):
        """
        Re-write to add auto creation option

        Methods:
         * action_create_sale_order
         * action_confirm of sale.order
        """
        appointment_id = super(business_appointment, self).create(values)
        ICPSudo = self.env['ir.config_parameter'].sudo()
        auto_creation = ICPSudo.get_param('ba_auto_sale_order', default='no')
        if auto_creation != "no":
            appointment_id.action_create_sale_order()
            if auto_creation == "confirmed":
                appointment_id.sudo().order_id.action_confirm()
            elif auto_creation == "sent":
                appointment_id.sudo().order_id.with_context(tracking_disable=True).write({'state': 'sent'})
        return appointment_id

    def write(self, values):
        """
        Re-write to cancel sale order if appointment is cancelled

        Methods:
         * action_cancel of sale order
        """
        res = super(business_appointment, self).write(values)
        if values.get("state") and values.get("state") in ["cancel"]:
            self.sudo().mapped("order_id").action_cancel()
        return res

    def action_create_sale_order(self):
        """
        The method to prepare a sale order by appointment values

        Methods:
         * _prepare_sale_order_vals
        """
        user_id = self.env.user
        self = self.sudo()
        for appointment in self:
            sale_values = appointment._prepare_sale_order_vals()
            if not sale_values.get("user_id"):
                sale_values["user_id"] = user_id.id
            order_id = self.env["sale.order"].create(sale_values)
            appointment.order_id = order_id

    def action_adapt_sale_order(self):
        """
        The method to prepare a sale order by appointment values

        Methods:
         * _prepare_sale_order_vals
        """
        self = self.sudo()
        for appointment in self:
            if appointment.order_id:
                appointment.order_id.order_line = False
                sale_values = appointment._prepare_sale_order_vals()
                appointment.order_id.write(sale_values)

    def _prepare_sale_order_vals(self):
        """
        The method to prepare sale order values based on appointment params

        Methods:
         * _return_main_line_qty()

        Returns:
         * dict

        Extra info:
         * Expected singleton()
        """
        self.ensure_one()
        related_main_product = self.service_id.product_id
        main_line = {
            "product_id": related_main_product.id,
            "product_uom": related_main_product.uom_id.id,
            "product_uom_qty": self._return_main_line_qty(),
        }
        order_line = [(0, 0, main_line)]
        for extra in self.extra_product_ids:
            extra_line = {
                "product_id": extra.product_id.id,
                "product_uom": extra.product_id.uom_id.id,
                "product_uom_qty": extra.product_uom_qty,
            }
            order_line.append((0, 0, extra_line))
        values = {
            "origin": self.name,
            "partner_id": self.partner_id.id,
            "pricelist_id": self.pricelist_id.id or self.partner_id.property_product_pricelist.id,
            "order_line": order_line,
        }
        user_id = self.sudo().resource_id.user_id
        if user_id:
            values.update({"user_id": user_id.id})
        return values

    def _return_main_line_qty(self):
        """
        The method to calculate main service quantity to be included into a sales order

        Returns:
         * float

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        pricing_method = self.resource_type_id.pricing_method
        qty = 1.00 # for per_planned_duration
        if pricing_method == "per_planned_duration":
            qty = self.duration
        elif pricing_method == "per_real_duration":
            if hasattr(self, "total_real_duration"):
                qty = self.total_real_duration
        return qty
