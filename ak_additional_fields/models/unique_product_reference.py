from odoo import models

class UniqueName(models.Model):
    _inherit = 'product.template'


    _sql_constraints = [
        (
            "reference_uniq",
            "unique(default_code)",
            "Product Reference must be unique across the database!",
        )

    ]