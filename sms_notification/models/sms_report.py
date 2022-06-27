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
from odoo import SUPERUSER_ID
import re
import operator
from odoo.exceptions import except_orm, Warning, RedirectWarning


class SmsReport(models.Model):
    """SMS report for every mobile number of sms."""

    _name = "sms.report"
    _inherit = 'sms.base.abstract'
    _description = "Model for sms report."
    _order = "id desc"
    _rec_name = "to"

    state = fields.Selection([
        ('new', 'Outgoing'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('undelivered', 'Undelivered'),
        ('failed', 'Failed'),
    ], string="Status", default="new")
    message = fields.Text(
        string="Information")
    sms_sms_id = fields.Many2one("wk.sms.sms", string="SMS")
    auto_delete = fields.Boolean(related="sms_sms_id.auto_delete", string="Auto Delete",
                                 help="Permanently delete this SMS after sending it,to save space.")
    status_hit_count = fields.Integer(
        string="Total count of trial of getting status using cron.")

    @api.model
    def cron_function_for_sms(self):
        pass
