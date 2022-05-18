from odoo import models

class UniqueName(models.Model):
    _inherit = 'account.account'


    _sql_constraints = [
        (
            "account_name_uniq",
            "unique(name)",
            "Account Name must be unique across the database!",
        )

    ]