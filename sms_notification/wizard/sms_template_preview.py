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
from odoo.tools.translate import _


class sms_template_preview(models.TransientModel):
    _name = "wk.sms.template.preview"
    _description = "SMS Template Preview"

    @api.model
    def _get_records(self):
        """
        Return Records of particular SMS Template's Model
        """

        sms_template_id = self._context.get('sms_template_id', False)
        if not sms_template_id:
            return []
        sms_template = self.env['wk.sms.template']
        template = sms_template.browse(int(sms_template_id))
        template_object = template.model_id
        model =  self.env[template_object.model]
        record_ids = model.search([], 0, 10, 'id')
        default_id = self._context.get('default_res_id')

        if default_id and default_id not in record_ids:
            record_ids.insert(0, default_id)
        return record_ids.name_get()

    @api.model
    def default_get(self, fields):
        result = super(sms_template_preview, self).default_get(fields)
        sms_template = self.env['wk.sms.template']
        template_id = self._context.get('sms_template_id')
        template = sms_template.browse(template_id)
        if 'res_id' in fields and not result.get('res_id'):
            records = self._get_records()
            result['res_id'] = records and records[0][0] or False # select first record as a Default
            result['model_id'] = template.model_id.id
        return result

    res_id = fields.Selection(_get_records, 'Sample Document')
    sms_body_html = fields.Text('Body', translate=True)
    model_id = fields.Many2one('ir.model', 'Applies to', help="The kind of document with this template can be used")
    name = fields.Char('Name', required=True)
    model = fields.Char(related="model_id.model", string='Related Document Model', store=True, readonly=True)

    @api.onchange("res_id")
    def on_change_res_id(self):
        if self.res_id and self._context.get('sms_template_id'):
            sms_template = self.env['wk.sms.template']
            template_id = self._context.get('sms_template_id')
            template = sms_template.browse(template_id)
            res_obj = self.env[self.model].browse(self.res_id)
            partner_id = res_obj.partner_id
            self.sms_body_html = template.get_body_data(res_obj,partner_id)
            self.name = template.name
