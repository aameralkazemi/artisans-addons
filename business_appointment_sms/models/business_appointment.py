import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

SMS_TEXT = _(u"This is the SMS sent to {}: <br/>")


def send_message_sms(self, partner_id=False, body_html='', condition=''):
    """Code to send sms to customer."""
    if not (condition):
        return
    print("send_message_sms----------------------------", body_html)
    ctx = dict(self._context or {})
    sms_template_objs = self.env["wk.sms.template"].search(
        [('condition', '=', condition), ('globally_access', '=', False)])
    gateway_id = self.env["sms.mail.server"].search(
        [], order='sequence asc', limit=1)
    for sms_template in sms_template_objs:
        mobile = sms_template._get_partner_mobile(partner_id)
        if mobile:
            smsData = sms_template.get_sms_vals(
                mobile, sms_template, gateway_id,
                obj=self
            )
            smsData.update({'msg': body_html})
            sms_sms_obj = self.env["wk.sms.sms"].create(smsData)
            print("sms_sms_obj----------", sms_sms_obj)
            sms_template.send_sms_using_template(
                mobile, sms_template, obj=self)


class SmsTemplate(models.Model):
    _inherit = 'wk.sms.template'

    condition = fields.Selection(
        selection_add=[('appointment', 'Appointment')])

    @api.depends('condition')
    def onchange_condition(self):
        super(SmsTemplate, self).onchange_condition()
        if self.condition:
            if self.condition == 'appointment':
                model_id = self.env['ir.model'].search(
                    [('model', '=', 'business.appointment')])
                self.model_id = model_id.id if model_id else False


class AlarmTask(models.Model):
    """
    The model to keep planned alarm queue
    """
    _inherit = "alarm.task"

    def _do_sms_reminder(self):
        """
        The method to parse template and send sms

        Methods:
         * _get_recipients
         * _get_partners_by_languages
         * _get_template_ctx of business.appointment
         * _render_template of mail.template
         * _send_sms of sms.api
         * message_post of mail.thread

        Extra info:
         * We send one message for each language
         * Expected singleton
        """
        self.ensure_one()
        sms_obj = self.env['sms.base.abstract']
        default_lang = self._context.get("lang") or self.env.user.lang
        appointment = self.appointment_id
        partners, internal = self._get_recipients()
        partners_by_languages = self._get_partners_by_languages(partners,
                                                                default_lang)
        for lang, partner_recordset in partners_by_languages.items():
            template_ctx = appointment._get_template_ctx(lang)
            template = self.with_context(template_ctx).alarm_id.sms_template_id
            body_html = template.with_context(template_ctx)._render_template(
                template.body,
                "business.appointment",
                [appointment.id],
            ).get(appointment.id)
            mobiles = partner_recordset.mapped("mobile")
            partner_names = ",".join(partner_recordset.mapped("name"))
            print("mobiles-00000000000000000", mobiles)
            if mobiles:
                try:
                    # sms_obj.with_context(action='send').send_sms_via_gateway(
                    #         body_html, mobiles, from_mob=None, sms_gateway=sms_obj.sms_gateway_config_id)
                    send_message_sms(appointment, appointment.partner_id, body_html,
                                     'appointment')
                    # self.env["sms.api"]._send_sms(mobiles, body_html)
                    self.appointment_id.message_post(
                        body=SMS_TEXT.format(partner_names) + body_html,
                        subject=SMS_TEXT.format(partner_names),
                        subtype_xmlid="mail.mt_note",
                    )
                except Exception as e:
                    _logger.error("SMS reminder is not sent {}".format(e))
        self._cr.commit()


class WebsiteBusinessAppointment(models.Model):
    """
    The model to keep settings of current (session) appointment
    """
    _inherit = "website.business.appointment"

    def _prepare_and_send_confirmation(self, approval_type):
        """
        The method to render template and send email/sms with confirmation code

        Args:
         * approval_type - char

        Methods:
         * _get_http_domain of website
         * _render_template of mail.template (and sms.template)
         * _send_sms of sms.api
         * build_email of ir.mail.server
         * send_email of ir.mail.server

        Extra info:
         * In case sms are not available but should be >> use email confirmation
         * Expected singleton
        """
        self.ensure_one()
        sms_obj = self.env['sms.base.abstract']
        lang = self.partner_id.lang or self._context.get(
            "lang") or self.env.user.lang
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        website_http_domain = self.website_id._get_http_domain() or base_url
        template_ctx = self._context.copy()
        template_ctx.update({
            "lang": lang,
            "base_url": base_url,
            "website_http_domain": website_http_domain,
        })
        if approval_type == "sms":
            template = self.sudo().with_context(lang=lang).env.ref(
                'business_appointment_website.sms_template_ba_confirmation_code',
                False,
            )
            if template:
                body_html = template.with_context(
                    template_ctx)._render_template(
                    template.body,
                    'website.business.appointment',
                    [self.id],
                ).get(self.id)
                mobile = self.partner_id and self.partner_id.mobile or self.mobile
                if mobile:
                    try:
                        # self.env["sms.api"]._send_sms([mobile], body_html)
                        sms_obj.with_context(
                            action='send').send_sms_via_gateway(
                            body_html, mobile, from_mob=None,
                            sms_gateway=sms_obj.sms_gateway_config_id)
                    except Exception as e:
                        _logger.error(
                            "Confirmation SMS is not sent {}".format(e))
                        approval_type = "email"
                else:
                    _logger.error(
                        "No mobile or phone are defined to send confirmation sms")
                    approval_type = "email"
        if approval_type == "email":
            template = self.sudo().with_context(lang=lang).env.ref(
                'business_appointment_website.email_template_confirmation_code',
                False,
            )
            if template:
                body_html = template.with_context(
                    template_ctx)._render_template_qweb(
                    template.body_html,
                    'website.business.appointment',
                    [self.id],
                ).get(self.id)
                subject = _("{}: Confirmation Code").format(
                    self.website_id.company_id.name)
                mail_server = self.env['ir.mail_server']
                try:
                    message = mail_server.build_email(
                        email_from=self.env.user.company_id.partner_id.email,
                        subject=subject,
                        body=body_html,
                        subtype='html',
                        email_to=[self.partner_id.email or self.email],
                    )
                    mail_server.send_email(message)
                except Exception as e:
                    _logger.error(
                        "Confirmation Email is not sent {}".format(e))
