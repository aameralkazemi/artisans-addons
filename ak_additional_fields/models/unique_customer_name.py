from odoo import models

class UniqueName(models.Model):
    _inherit = 'res.partner'


    _sql_constraints = [
        (
            "name_uniq",
            "unique(name)",
            "Name must be unique across the database!",
        )

    ]