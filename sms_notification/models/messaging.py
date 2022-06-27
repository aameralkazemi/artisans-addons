# -*- coding: utf-8 -*-
##########################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2017-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
##########################################################################

import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


def send_message_sms(self, partner_id=False, condition=''):
    """Code to send sms to customer."""
    if not (condition):
        return
    sms_template_objs = self.env["wk.sms.template"].search(
        [('condition', '=', condition), ('globally_access', '=', False)])
    for sms_template_obj in sms_template_objs:
        mobile = sms_template_obj._get_partner_mobile(partner_id)
        if mobile:
            sms_template_obj.send_sms_using_template(
                mobile, sms_template_obj, obj=self)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        result = super(SaleOrder, self).action_confirm()
        for res in self:
            send_message_sms(res, res.partner_id, 'order_confirm')
        return result

    def action_cancel(self):
        result = super(SaleOrder, self).action_cancel()
        for res in self:
            send_message_sms(res, res.partner_id, 'order_cancel')
        return result

    def write(self, vals):
        result = super(SaleOrder, self).write(vals)
        for res in self:
            if vals.get('state', False) == 'sent':
                send_message_sms(res, res.partner_id, 'order_placed')
        return result


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def write(self, vals):
        result = super(StockPicking, self).write(vals)
        for res in self:
            if vals.get('date_done', False):
                send_message_sms(res, res.partner_id, 'order_delivered')
        return result


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        result = super(AccountMove, self).action_post()
        for res in self:
            send_message_sms(res, res.partner_id, 'invoice_vaildate')
        return result


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def action_create_payments(self):
        res = super(AccountPaymentRegister, self).action_create_payments()
        if self._context.get('active_model') == 'account.move':
            invoice_ids = self.env['account.move'].browse(self._context.get('active_ids', []))
            paid_invoices = invoice_ids.filtered(lambda move: move.is_invoice(include_receipts=True) and move.payment_state in ('partial','paid'))[0]
            send_message_sms(paid_invoices, paid_invoices.partner_id, 'invoice_paid')
        return res
