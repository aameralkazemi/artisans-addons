from odoo import models, fields

class Partnerpage(models.Model):
    _inherit = 'business.appointment'

    checkin = fields.Boolean(string="Check in")


