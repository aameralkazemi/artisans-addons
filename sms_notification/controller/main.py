# -*- coding: utf-8 -*-
##########################################################################
#
#    Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
##########################################################################
import calendar
from odoo import models, http, fields, api, _
from odoo.http import request
from werkzeug.urls import url_join
import logging
_logger = logging.getLogger(__name__)

gateway_blog_link = {'sms_notification': "https://webkul.com/blog/odoo-sms-notification/",
                    'clicksend': "https://webkul.com/blog/odoo-clicksend-sms-gateway/",
                    'infobip': "https://webkul.com/blog/odoo-sms-infobip-gateway/",
                    'messagebird': "https://webkul.com/blog/odoo-messagebird-sms-gateway/",
                    'mobily': "https://webkul.com/blog/mobily-sms-gateway/",
                    'msegat': "https://webkul.com/blog/odoo-sms-notification/",
                    'msg91': "https://webkul.com/blog/msg91-gateway/",
                    'netelip': "https://webkul.com/blog/odoo-netelip-sms-gateway/",
                    'nexmo': "https://webkul.com/blog/odoo-nexmo-sms-gateway/",
                    'plivo': "https://webkul.com/blog/odoo-sms-plivo-gateway/",
                    'skebby': "https://webkul.com/blog/odoo-skebby-sms-gateway/",
                    'smshub': "https://webkul.com/blog/odoo-smsgatewayhub-sms-gateway/",
                    'textlocal': "https://webkul.com/blog/odoo-textlocal-sms-gateway/",
                    'twilio': "https://webkul.com/blog/odoo-sms-twilio-gateway/",
                    'twilio_whatsapp': "https://webkul.com/blog/odoo-twilio-whatsapp-integration/"
                    }
class SMSNotificationDashboard(http.Controller):

    def get_reports_count(self, reports, state):
        if state == 'all':
            return len(reports)
        else:
            return len(reports.filtered(lambda rp: rp.state == state))

    @http.route(['/sms_notification/dashboard_data'], type="json", auth="user")
    def load_dashboard(self,line_stage='all', pie_stage='all', days=7,**kw):
        today = fields.date.today()
        counts = {}
        labels = []
        sms_reports = request.env['sms.report'].search([])
        data = []
        for i in range(days-1,-1,-1):
            date = fields.Datetime.subtract(today,days=i)
            cnt = [0]*days
            counts = {}
            index = date.strftime('%A') if days == 7 else date.strftime('%d')
            labels.append(index)
            cnt[i] = len(sms_reports.filtered(lambda rp: rp.state == line_stage and rp.create_date.date() == date))
            counts['count'] = cnt
            data.append(counts)
        total_count = len(sms_reports)
        stages = ['new','sent','delivered','undelivered','failed']
        stage_counts = []
        for stage in stages:
            stage_counts.append(len(sms_reports.filtered(lambda rp: rp.state == stage)))
        gateway_data = {}
        connected_gateways = request.env['sms.mail.server'].search([])
        for cnt_gateway in connected_gateways:
            reports = request.env['sms.report'].search([('sms_gateway_config_id.gateway','=',cnt_gateway.gateway)])
            web_base_url = request.env['sms.mail.server'].get_base_url()
            gateway_data[cnt_gateway.description] = {
                'id': cnt_gateway.id,
                'name': cnt_gateway.description,
                'image': '/sms_notification/static/sms_gateways/'+cnt_gateway.gateway+'.png',
                'blog_link': gateway_blog_link.get(cnt_gateway.gateway) or "https://webkul.com/blog/odoo-sms-notification/",
                'edit_link': url_join(web_base_url, f'/web#id={cnt_gateway.id}&model=sms.mail.server&view_type=form'),
                'total_count' : self.get_reports_count(reports, 'all'),
                'new_count': self.get_reports_count(reports, 'new'),
                'sent_count': self.get_reports_count(reports, 'sent'),
                'delivered_count': self.get_reports_count(reports, 'delivered'),
                'undelivered_count': self.get_reports_count(reports, 'undelivered'),
                'failed_count': self.get_reports_count(reports, 'failed'),
            }
        return {
            'line_data': {'labels':labels,'data':data},
            'gateway_data': gateway_data,
            'connected_count': len(connected_gateways),
            'total_count': total_count,
            'sent_count': stage_counts[1],
            'delivered_count': stage_counts[2],
            'undelivered_count': stage_counts[3],
            'failed_count': stage_counts[4],
        }
