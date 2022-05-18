from odoo import models

class UniqueName(models.Model):
    _inherit = 'product.template'


    _sql_constraints = [
        (
            "product_name_uniq",
            "unique(name)",
            "Product Name must be unique across the database!",
        )

    ]