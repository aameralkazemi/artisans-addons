# -*- coding: utf-8 -*-
##############################################################################
#
# Odoo, Open Source Management Solution
# Copyright (C) 2016 Webkul Software Pvt. Ltd.
# Author : www.webkul.com
#
##############################################################################
import logging
import requests
import json
from urllib3.exceptions import HTTPError
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning

_logger = logging.getLogger(__name__)

def send_sms_using_msegat(body_sms, mob_no, from_mob=None, sms_gateway=None):
    '''
    This function is designed for sending sms using Msegat SMS API.

    :param body_sms: body of sms contains text
    :param mob_no: Here mob_no must be string having one or more seprated by (,)
    :param from_mob: sender mobile number or id used in Msegat API
    :param sms_gateway: sms.mail.server config object for Msegat Credentials
    :return: response dictionary if sms successfully sent else empty dictionary
    '''
    if not (sms_gateway and body_sms and mob_no):
        return {}
    if sms_gateway.gateway == "msegat":
        if sms_gateway.msegat_api_key and sms_gateway.username and sms_gateway.userSender:
            if isinstance(mob_no, list):
                mob_no = ','.join(mob_no)
            mob_no = mob_no.replace('+', '')
            url = "https://www.msegat.com/gw/sendsms.php"
            data = {
                'apiKey': sms_gateway.msegat_api_key,
                'userName': sms_gateway.username,
                'userSender': sms_gateway.userSender,
                'numbers': mob_no,
                'msg': body_sms,
                'reqBulkId': 'true',
            }
            headers = {
                "Content-type": "application/json",
            }
            try:
                response = requests.post(url, data=json.dumps(data), headers=headers)
                return response.json()
            except HTTPError as e:
                logging.info(
                    '---------------Msegat HTTPError----------------------', exc_info=True)
                _logger.info(
                    "---------------Msegat HTTPError While Sending SMS ----%r---------", e)
            except Exception as e:
                logging.info(
                    '---------------Msegat Exception While Sending SMS ----------', exc_info=True)
                _logger.info(
                    "---------------Msegat Exception While Sending SMS -----%r---------", e)
    return {}


class SmsSms(models.Model):
    """SMS sending using Msegat SMS Gateway."""

    _inherit = "wk.sms.sms"
    _name = "wk.sms.sms"
    _description = "Msegat SMS"


    def send_sms_via_gateway(
            self, body_sms, mob_no, from_mob=None, sms_gateway=None):
        self.ensure_one()
        gateway_id = sms_gateway if sms_gateway else super(
            SmsSms, self).send_sms_via_gateway(
            body_sms, mob_no, from_mob=from_mob, sms_gateway=sms_gateway)
        if gateway_id:
            if gateway_id.gateway == 'msegat':
                for element in mob_no:
                    for mobi_no in element.split(','):
                        response = send_sms_using_msegat(
                            body_sms, mobi_no, from_mob=from_mob,
                            sms_gateway=gateway_id)
                        message_data = response.get('message')
                        sms_report_obj = self.env["sms.report"].create(
                            {
                                'to': mobi_no, 'msg': body_sms,
                                'sms_sms_id': self.id,
                                "auto_delete": self.auto_delete,
                                'sms_gateway_config_id': gateway_id.id})
                        vals = {'state':'undelivered'}
                        if response.get('message') in ['Success']:
                            code, sms_id = response.get("code").split('-')
                            vals['msegat_sms_id'] = sms_id
                            vals['state'] = 'sent'
                            vals['message'] = False
                        else:
                            vals.update({'state': 'failed','message':response.get("message")})
                        if sms_report_obj:
                            sms_report_obj.write(vals)
                    else:
                        self.write({'state': 'error'})
                else:
                    self.write({'state': 'sent'})
            else:
                gateway_id = super(SmsSms, self).send_sms_via_gateway(
                    body_sms, mob_no, from_mob=from_mob,
                    sms_gateway=sms_gateway)
        else:
            _logger.info(
                "----------------------------- SMS Gateway not found ----------\
                ---------------")
        return gateway_id


class SmsReport(models.Model):
    """SMS report."""

    _inherit = "sms.report"

    msegat_sms_id = fields.Char("Msegat SMS ID")

    @api.model
    def cron_function_for_sms(self):
        _logger.info(
            "************** Cron Function For Msegat SMS *******************")
        all_sms_report = self.search([('state', 'in', ('sent', 'new')),('sms_gateway','=','msegat')])
        for sms in all_sms_report:
            sms_sms_obj = sms.sms_sms_id if sms.sms_sms_id else False
            if not sms.msegat_sms_id:
                sms.send_now()
        super(SmsReport, self).cron_function_for_sms()
        return True

    def send_sms_via_gateway(
            self, body_sms, mob_no, from_mob=None, sms_gateway=None):
        self.ensure_one()
        gateway_id = sms_gateway if sms_gateway else super(
            SmsReport, self).send_sms_via_gateway(
            body_sms, mob_no, from_mob=from_mob, sms_gateway=sms_gateway)
        if gateway_id:
            if gateway_id.gateway == 'msegat':
                if mob_no:
                    for element in mob_no:
                        count = 1
                        for mobi_no in element.split(','):
                            if count == 1:
                                self.to = mobi_no
                                rec = self
                            else:
                                rec = self.create({
                                    'to': mobi_no, 'msg': body_sms,
                                    "auto_delete": self.auto_delete,
                                    'sms_gateway_config_id': gateway_id.id})
                            response = send_sms_using_msegat(
                                body_sms, mobi_no, from_mob=from_mob,
                                sms_gateway=gateway_id)
                            message_data = response.get('message')
                            vals = {'state':'undelivered'}
                            if response.get('message') in ['Success']:
                                code, sms_id = response.get("code").split('-')
                                vals['msegat_sms_id'] = sms_id
                                vals['state'] = 'sent'
                                vals['message'] = False
                            else:
                                vals.update({'state': 'failed','message':response.get("message")})
                            rec.write(vals)
                            count += 1
                else:
                    self.write({'state': 'sent'})
            else:
                gateway_id = super(SmsReport, self).send_sms_via_gateway(
                    body_sms, mob_no, from_mob=from_mob,
                    sms_gateway=sms_gateway)
        return gateway_id
