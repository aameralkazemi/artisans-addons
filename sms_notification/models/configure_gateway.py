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


class SmsMailServer(models.Model):
    """This class is design for configuring the sms mail server."""

    _name = "sms.mail.server"
    _description = "Module for sms mail server configuration."
    _rec_name = 'description'

    @api.model
    def get_reference_type(self):
        return []

    description = fields.Char(string="Description", required=True)
    sequence = fields.Integer(
        string='Priority', help="Default Priority will be 10.", default=10)
    sms_debug = fields.Boolean(
        string="Debugging", help="If enabled, the error message of sms gateway will be written to the log file")
    user_mobile_no = fields.Char(
        string="Mobile No. (To Receive Test SMS)", help="Ten digit mobile number with country code(e.g +91)")
    gateway = fields.Selection('get_reference_type', string="SMS Gateway")
