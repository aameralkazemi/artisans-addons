# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request

from odoo.addons.business_appointment_website.controllers.main import CustomerPortal
from odoo.addons.website_sale.controllers.main import WebsiteSale

WebsiteSaleInstance = WebsiteSale()


class CustomerPortal(CustomerPortal):
    """
    Overwritting the pass prices and pricelists
    """
    def _get_extra_options_ba_values(self):
        """
        Re-write to pass whether pricing information option is turned on
        """
        values = super(CustomerPortal, self)._get_extra_options_ba_values()
        values.update({"ba_pricelists_prices": request.website.ba_pricelists_prices,})
        return values

    def _prepare_extra_values_for_new_reservation(self, session_appointment_id):
        """
        Overwrite to add pricelist

        Methods:
         * ba_get_cur_pricelist of website
        """
        values = super(CustomerPortal, self)._prepare_extra_values_for_new_reservation(session_appointment_id)
        pricelist_id = request.website.ba_get_cur_pricelist(session_appointment_id)
        values.update({"pricelist_id": pricelist_id and pricelist_id.id or False})
        return values

    def _prepare_extra_values_slots(self, session_appointment_id):
        """
        Re-write to add pricelist values

        Methods:
         * ba_get_cur_pricelist
        """
        values = super(CustomerPortal, self)._prepare_extra_values_slots(session_appointment_id=session_appointment_id)
        if request.website.ba_pricelists_prices:
            pricelist_id = request.website.ba_get_cur_pricelist(session_appointment_id)
            values.update({"ba_pricelist_id": pricelist_id and pricelist_id.id or False})
        return values

    def _prepare_full_appointment_vals(self, appointment_id):
        """
        Re-write to get portal sale order if user has rights for that
        """
        vals = super(CustomerPortal, self)._prepare_full_appointment_vals(appointment_id=appointment_id)
        show_order = False
        try:
            order_id = appointment_id.order_id
            if order_id and not order_id.check_access_rule("read"):
                show_order = True
        except :
            show_order = False
        vals.update({"show_order": show_order})
        return vals

    @http.route(['/appointments/change_pricelist/<model("product.pricelist"):pl_id>'], type='http', auth="public", 
                 website=True, sitemap=False)
    def ba_pricelist_change(self, pl_id, **post):
        """
        The method to change pricelist

        Methods:
         * _prepare_session_order 
         * pricelist_change of website_sale controller
        """
        if (pl_id.selectable or pl_id == request.env.user.partner_id.property_product_pricelist) \
                and request.website.is_pricelist_available(pl_id.id):
            session_appointment_id = self._prepare_session_order() 
            session_appointment_id.pricelist_id = pl_id
            if session_appointment_id.sudo().url_reservation_ids:
                session_appointment_id.sudo().url_reservation_ids.write({"pricelist_id": pl_id.id})
        res = WebsiteSaleInstance.pricelist_change(pl_id, **post)
        return request.redirect(request.httprequest.referrer or '/appointments')


