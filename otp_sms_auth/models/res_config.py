# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   If not, see <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import api, fields, models, _

class WebsiteOTPSettings(models.TransientModel):
    _inherit = 'website.otp.settings'

    otp_notification_mode = fields.Selection([('sms', 'SMS'), ('email', 'Email'), ('both', 'Both')], string="OTP Notification Mode",
                                  help="""Send OTP to customer via.
                                    * [SMS] OTP will be send to the user via SMS
                                    * [Email] OTP will be send to the user via Email
                                    * [Both] OTP will be send to the user via SMS/Email Mode""")

    # @api.multi
    def set_values(self):
        super(WebsiteOTPSettings, self).set_values()
        IrDefault = self.env['ir.default'].sudo()
        IrDefault.set('website.otp.settings','otp_notification_mode', self.otp_notification_mode)
        return True

    # @api.multi
    def get_values(self):
        res = super(WebsiteOTPSettings, self).get_values()
        IrDefault = self.env['ir.default'].sudo()
        res.update({
            'otp_notification_mode':IrDefault.get('website.otp.settings','otp_notification_mode', self.otp_notification_mode),
        })
        return res
