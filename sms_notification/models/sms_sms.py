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

from odoo import SUPERUSER_ID, api
import re
from functools import reduce
import operator
from odoo.exceptions import Warning
from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)


class SmsBase(models.AbstractModel):
    _name = "sms.base.abstract"
    _description = "Contains the logic shared between models which allows to send sms."

    @api.depends("sms_gateway_config_id")
    def get_sms_gateway_name(self):
        for rec in self:
            rec.sms_gateway = rec.sms_gateway_config_id.gateway if rec.sms_gateway_config_id else ""

    @api.model
    def _get_default_config_sms_gateway(self):
        return self.env["sms.mail.server"].search([], order='sequence asc', limit=1)

    to = fields.Char("To:", required=True)
    by = fields.Char("From:")
    msg = fields.Text("Message:", required=True)
    sms_gateway_config_id = fields.Many2one(
        'sms.mail.server', string="SMS Gateway", default=_get_default_config_sms_gateway)
    sms_gateway = fields.Char(
        compute='get_sms_gateway_name', string="Gateway Name", store=True)

    
    def send_sms_via_gateway(self, body_sms, mob_no, from_mob=None, sms_gateway=None):
        gateway_obj = sms_gateway if sms_gateway else self.env[
            "sms.mail.server"].search([], order='sequence asc', limit=1)
        if gateway_obj and not gateway_obj.gateway:
            raise Warning("SMS configuration has no gateway.")
        elif gateway_obj and gateway_obj.gateway:
            return gateway_obj
        else:
            _logger.info(
                "***************** No SMS Gateway Configuration  *******************")
            return False

    
    def send_now(self):
        for obj in self:
            body_sms = obj.msg
            mob_no = [obj.to]
            obj.with_context(action='send').send_sms_via_gateway(
                body_sms, mob_no, from_mob=None, sms_gateway=obj.sms_gateway_config_id)

    
    def retry(self):
        for obj in self:
            body_sms = obj.msg
            mob_no = [obj.to]
            obj.with_context(action='retry').send_sms_via_gateway(
                body_sms, mob_no, from_mob=None, sms_gateway=obj.sms_gateway_config_id)

    def set_error_message(self, gateway_id, errorMsg):
        ctx = dict(self._context or {})
        ctx['sms_error'] = errorMsg
        gateway_id = gateway_id.with_context(ctx)
        return gateway_id


class SmsSms(models.Model):
    """SMS sending using SMS mail server."""

    _name = "wk.sms.sms"
    _inherit = 'sms.base.abstract'
    _description = "Model for Sms."
    _rec_name = "group_type"
    _order = "id desc"

    @api.depends("sms_report_ids")
    def _get_total_sms_status_count(self):
        sent_count = 0
        delivered_count = 0
        undelivered_count = 0
        for rec in self:
            for sms_report in rec.sms_report_ids:
                if sms_report.state == "sent":
                    sent_count += 1
                if sms_report.state == "delivered":
                    delivered_count += 1
                if sms_report.state == "undelivered":
                    undelivered_count += 1
            rec.total_sent_sms = sent_count
            rec.total_delivered_sms = delivered_count
            rec.total_undelivered_sms = undelivered_count

    name = fields.Char(string="Title")
    state = fields.Selection([
        ('new', 'Draft'),
        ('sent', 'Sent'),
        ('error', 'Error'),
    ], "State", default='new')
    auto_delete = fields.Boolean(
        "Auto Delete", help="Permanently delete all SMS after sending,to save space.", default=True)
    group_type = fields.Selection([('group', 'Group'),
                                   ('multiple', 'Multiple Members'),
                                   ('individual', 'Individual Member/Number')], string="Send SMS To", default='group', help="This field is used to send the message for a single customer or group of customer.")
    group_ids = fields.Many2one("sms.group",  string="Group")
    partner_id = fields.Many2one("res.partner", string="Recipient")
    partner_ids = fields.Many2many(
        "res.partner", "sms_partner_relation", 'sms_id', 'receiver_id', string="Recipients")

    sms_report_ids = fields.One2many(
        "sms.report", "sms_sms_id", string="SMS Delivery Report")

    total_sent_sms = fields.Integer(
        string="Sent SMS", compute=_get_total_sms_status_count)
    total_delivered_sms = fields.Integer(
        string="Delivered SMS", compute=_get_total_sms_status_count)
    total_undelivered_sms = fields.Integer(
        string="Undelivered SMS", compute=_get_total_sms_status_count)
    template_id = fields.Many2one(
        'wk.sms.template', string="Template", domain="[('globally_access', '=', True)]")

    @api.onchange("template_id")
    def onchange_tempalte_id(self):
        if self.template_id:
            self.msg = self.template_id.sms_body_html
        else:
            self.msg = False

    def _get_partner_mobile(self, partner):
        company_country_calling_code = self.env.user.company_id.country_id.phone_code
        managed_calling_code = self.env['ir.config_parameter'].sudo().get_param(
            'sms_notification.is_phone_code_enable', 'False') == 'True'
        if managed_calling_code:
            return partner.mobile
        if partner.country_id and partner.country_id.phone_code:
            country_calling_code = partner.country_id.phone_code
        else:
            country_calling_code = company_country_calling_code
        return "+{code}{mobile}".format(code=country_calling_code, mobile=partner.mobile)

    def _get_partner_mobile_numbers(self, group):
        return [self._get_partner_mobile(partner) for partner in group.member_ids if partner.mobile]

    @api.onchange('group_ids')
    def add_group_member_number(self):
        phone_lists = [self._get_partner_mobile_numbers(
            group) for group in self.group_ids if self.group_ids]
        combined_list = reduce(
            operator.add, phone_lists) if phone_lists else []
        self.to = self.get_mobile_number(list(set(combined_list)))

    @api.onchange('partner_id')
    def add_partner_number(self):
        if self.partner_id:
            self.to = self._get_partner_mobile(
            self.partner_id) if self.partner_id.mobile else ""

    @api.onchange('partner_ids')
    def add_partner_member_number(self):
        self.to = self.get_mobile_number([self._get_partner_mobile(partner)
                                          for partner in self.partner_ids if partner.mobile])

    @api.model
    def get_mobile_number(self, mob_no):
        # Here mob_no is a list of str of mobile number
        if self.sms_gateway_config_id.gateway == "plivo":
            return '<'.join(mob_no)
        elif self.sms_gateway_config_id.gateway == "clicksend":
            return ','.join(mob_no)
        else:
            return ','.join(mob_no)

    @api.onchange('sms_gateway_config_id')
    def onchange_sms_gateway_config_id(self):
        if self.group_type == "multiple":
            self.add_partner_member_number()
        elif self.group_type == "group":
            self.add_group_member_number()
        elif self.group_type == "individual":
            self.add_partner_number()

    @api.onchange("group_type")
    def blank_number_from_to(self):
        self.to = ""

    
    def save_as_draft(self):
        self.ensure_one()
        return

    
    def action_view_sent_sms(self):
        for rec in self:
            action = self.env["ir.actions.act_window"]._for_xml_id(
                "sms_notification.sms_report_action")
            action['domain'] = "[('sms_sms_id', '=', %s), ('state', '=', 'sent')]" % rec.id
            return action

    
    def action_view_delivered_sms(self):
        for rec in self:
            action = self.env["ir.actions.act_window"]._for_xml_id(
                "sms_notification.sms_report_action")
            action['domain'] = "[('sms_sms_id', '=', %s), ('state', '=', 'delivered')]" % rec.id
            return action

    
    def action_view_undelivered_sms(self):
        for rec in self:
            action = self.env["ir.actions.act_window"]._for_xml_id(
                "sms_notification.sms_report_action")
            action['domain'] = "[('sms_sms_id', '=', %s), ('state', '=', 'undelivered')]" % rec.id
            return action
