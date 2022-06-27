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


class SmsGroup(models.Model):

    _name = "sms.group"
    _description = "This module is used for create the group of customer to send message"

    name = fields.Char(string="Group Name", required=True)
    member_type = fields.Selection([('customer', 'Customer'),
                                    ('supplier', 'Supplier'),
                                    ('any', 'Any')], string="Member Type", default="customer", required=True)
    member_ids = fields.Many2many(comodel_name="res.partner", relation='sms_member_group',
                                  column1='member_id', column2='partner_id', string="Members", required=True)
    total_members = fields.Integer(
        compute='get_total_members', string="Total Members", store=True)

    
    @api.depends("member_ids")
    def get_total_members(self):
        self.total_members = len(self.member_ids)

    @api.onchange('member_type')
    def onchange_member_type(self):
        self.member_ids = False
        res = {}
        if self.member_type == 'customer':
            res['domain'] = {'member_ids': [('customer_rank','>', 0)]}
        if self.member_type == 'supplier':
            res['domain'] = {'member_ids': [('supplier_rank','>', 0)]}
        if self.member_type == 'any':
            res['domain'] = {'member_ids': []}
        return res
