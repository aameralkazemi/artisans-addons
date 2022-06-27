# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   If not, see <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import models, _

class SendOtp(models.TransientModel):
    _name = 'send.otp'
    _description = 'Send Otp'
    _MAIL_TEMPLATE_FIELDS = ['subject', 'body_html', 'email_from', 'email_to',
                             'email_cc', 'reply_to', 'scheduled_date', 'attachment_ids']

    def email_send_otp(self, email, userName, otp):
        if not userName:
            userObj = self.env['res.users'].sudo().search([('login', '=', email)])
            userName = userObj.name
        uid = self.sudo()._uid
        templateObj = self.env.ref('otp_auth.email_template_edi_otp', raise_if_not_found=False)
        ctx = dict(templateObj._context or {})
        ctx['name'] = userName or 'User'
        ctx['otp'] = otp
        ctx['email_to'] = email
        res= templateObj.sudo().with_context(ctx).send_mail(self.id, True)
        return True
