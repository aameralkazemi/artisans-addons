from odoo import models

class UniqueName(models.Model):
    _inherit = 'res.partner'


    _sql_constraints = [
        (
            "code_uniq",
            "unique(mobile)",
            "Code must be unique across the database!",
        )

    ]