# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   If not, see <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import api, models, _
from odoo.http import request

import logging
_logger = logging.getLogger("------ SEND OTP -------")

class SendOtp(models.TransientModel):
    _inherit = 'send.otp'

    # @api.multi
    def email_send_otp(self, email, userName, otp):
        otp_notification_mode = self.env['ir.default'].sudo().get('website.otp.settings', 'otp_notification_mode')
        if otp_notification_mode != 'sms':
            res = super(SendOtp, self).email_send_otp(email, userName, otp)
        return True

    def setDataSession(self, otpdata=False):
        request.session['otpdata'] = False
        request.session['context']['otpdata'] = False
        if otpdata:
            request.session['otpdata'] = otpdata
            request.session['context']['otpdata'] = otpdata
        return True

    # @api.multi
    def sms_send_otp(self, mobile, userName, otp, phone_code):
        otp_notification_mode = self.env['ir.default'].sudo().get('website.otp.settings', 'otp_notification_mode')
        if otp_notification_mode != 'email':
            try:
                if not userName:
                    userObj = self.env["res.users"].sudo().search([("mobile", "=", mobile)], limit=1)
                    userName = userObj.name
                else:
                    userObj = self.env['res.users'].sudo().browse(self.sudo()._uid)
                    # userName = userObj.name
                sms_template_objs = self.env["wk.sms.template"].sudo().search(
                    [('condition', '=', 'otp'),('globally_access','=',False)])
                if mobile:
                    for sms_template_obj in sms_template_objs:
                        ctx = dict(sms_template_obj._context or {})
                        ctx['name'] = userName or 'User'
                        ctx['otp'] = otp
                        if phone_code:
                            if mobile[:1] == '0':
                                mobile = "+{}{}".format(phone_code, mobile[1:])
                            elif "+" not in mobile:
                                mobile = "+{}{}".format(phone_code, mobile)
                        (sms_template_obj,(ctx))
                        response = sms_template_obj.with_context(ctx).send_sms_using_template(
                            mobile, sms_template_obj, obj=userObj)
                        return response
            except Exception as e:
                _logger.info("---Exception raised : %r while sending OTP", e)
        return self
