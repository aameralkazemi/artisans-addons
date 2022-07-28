# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CustomPosReceipt(models.AbstractModel):
    _name = 'report.customer_invoice_pdf_report.custom_pos_receipt'

    @api.model
    def _get_report_values(self, docids, data=None):
        print("_get_report_values------------------------------")
        docs = self.env['account.move'].browse(docids)

        qr_code_urls = {}
        for invoice in docs:
            print("invoice------------------------------",invoice)
            if invoice.display_qr_code:
                new_code_url = invoice.generate_qr_code()
                if new_code_url:
                    qr_code_urls[invoice.id] = new_code_url
        print("qr_code_urls------------------------------", qr_code_urls)
        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'docs': docs,
            'qr_code_urls': qr_code_urls,
        }
