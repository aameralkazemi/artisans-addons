# -*- coding: utf-8 -*-
##############################################################################
#
#    SLTECH ERP SOLUTION
#    Copyright (C) 2020-Today(www.slecherpsolution.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, models

class AccountMove(models.Model):
    _inherit = "account.move"

    def get_sale_number(self):
        self.env.cr.execute("select id from sale_order where name=\'%s\'" % self.invoice_origin)
        result = self.env.cr.dictfetchone()
        if result:
            return self.env['sale.order'].browse(result['id'])

    def get_delivery_order(self):
        self.env.cr.execute("select id from sale_order where name=\'%s\'" % self.invoice_origin)
        result = self.env.cr.dictfetchone()
        if result:
            sale_id = self.env['sale.order'].browse(result['id'])
            if sale_id.picking_ids:
                return sale_id.picking_ids[0]



    def get_sale_details(self):
        self.env.cr.execute("select id from sale_order where name=\'%s\'" % self.invoice_origin)
        result = self.env.cr.dictfetchone()
        if result:
            sale_id = self.env['sale.order'].browse(result['id'])
            if sale_id:
                delivery_name = ""
                if sale_id.picking_ids and sale_id.picking_ids[0].name:
                    delivery_name = sale_id.picking_ids and sale_id.picking_ids[0].name
                return {
                    'sale_number': sale_id.name,
                    'delivery_order_name': delivery_name,

                }
        return {
            'sale_number': '',
            'delivery_order_name': '',
        }

