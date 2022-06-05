#coding: utf-8

from odoo import fields, models

class website(models.Model):
    """
    Overwrite to keep configuration for time slots
    """
    _inherit = "website"

    ba_pricelists_prices = fields.Boolean(string="Pricelists and Prices", default=True)

    def ba_get_cur_pricelist(self, session_appointment_id=False):
        """
        The method to wrap check for session order pricelist
        
        Args:
         * session_appointment_id - website.business.appointment

        Methods:
         * get_pricelist_available
         * get_current_pricelist

        Returns:
         * product.pricelist object
        """
        pl = None
        available_pricelists = self.get_pricelist_available()
        if session_appointment_id and session_appointment_id.pricelist_id \
                and session_appointment_id.pricelist_id in available_pricelists:
            pl = session_appointment_id.pricelist_id
        else:
            pl = self.get_current_pricelist()
        return pl


