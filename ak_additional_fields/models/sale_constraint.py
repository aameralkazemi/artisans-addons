from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"


    @api.constrains('order_line')
    def _check_exist_product_in_line(self):
      for purchase in self:
          exist_product_list = []
          for line in purchase.order_line:
             if line.product_id.id in exist_product_list:
                raise ValidationError(('Product should be one per line.'))
             exist_product_list.append(line.product_id.id)