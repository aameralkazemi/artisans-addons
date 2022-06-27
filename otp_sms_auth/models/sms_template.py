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

from odoo import models, fields, api, _

class SmsTemplate(models.Model):
    _inherit = 'wk.sms.template'

    condition = fields.Selection(selection_add=[('otp', 'OTP')])

    @api.depends('condition')
    def onchange_condition(self):
        super(SmsTemplate, self).onchange_condition()
        if self.condition:
            if self.condition == 'otp':
                model_id = self.env['ir.model'].search(
                    [('model', '=', 'send.otp')])
                self.model_id = model_id.id if model_id else False
