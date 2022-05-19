#coding: utf-8

from odoo import api, fields, models
from odoo.addons.phone_validation.tools import phone_validation

class appointment_contact_info(models.AbstractModel):
    """
    The model to keep contact info required for appointment

    Extra info:
     * pricelist_id is not included into _contact_fields fields purposefully to avoid situation of re-writing that
       for partner automatically (e.g. in case of promo code apply)
    """
    _name = "appointment.contact.info"
    _description = "Contact Info"
    _rec_name = "partner_id"
    _contact_fields = [
        ("contact_name", "name", "char"), 
        ("email", "email", "char"),
        ("phone", "phone", "char"),
        ("mobile", "mobile", "char"),
        ("street", "street", "char"),
        ("street2", "street2", "char"),
        ("zipcode", "zip", "char"),
        ("city", "city", "char"),
        ("state_id", "state_id", "many2one"),
        ("country_id", "country_id", "many2one"),
        ("function", "function", "char"),
        ("title", "title", "many2one"),
    ]

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        """
        Onchange method for partner_id
        
        Methods:
         * _return_partner_values

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        values = self._return_partner_values()
        if self.partner_id:
            values.update({"pricelist_id": self.partner_id.property_product_pricelist.id})
        return {"value": values}

    @api.onchange("email", "mobile", "phone")
    def _onchange_email(self):
        """
        Onchange method for email, mobile, phone --> to select a new partner if exists

        Methods:
         * _apapt_phone_number
        """
        for wiz in self:
            wiz._apapt_phone_number("phone")
            wiz._apapt_phone_number("mobile")
            if not wiz.partner_id and (wiz.email or wiz.mobile or wiz.phone):
                partner_id = wiz._check_existing_duplicates(wiz.email, wiz.mobile, wiz.phone)
                if partner_id:
                    wiz.partner_id = partner_id

    def _inverse_phone(self):
        """
        Inverse method for phone to keep international format

        Methods:
         * _apapt_phone_number
        """
        for record in self:
            record._apapt_phone_number("phone")

    def _inverse_mobile(self):
        """
        Inverse method for mobil to keep international format

        Methods:
         * _apapt_phone_number
        """
        for record in self:
            record._apapt_phone_number("mobile")

    description = fields.Text(string="Notes",)
    partner_id = fields.Many2one("res.partner", string="Contact", required=False,)
    contact_name = fields.Char("Contact Name")
    email = fields.Char("Email")
    phone = fields.Char('Phone', inverse=_inverse_phone,)
    mobile = fields.Char('Mobile', inverse=_inverse_mobile,)
    street = fields.Char('Street')
    street2 = fields.Char('Street2')
    zipcode = fields.Char('Zip')
    city = fields.Char('City')
    state_id = fields.Many2one("res.country.state", string='State')
    country_id = fields.Many2one('res.country', string='Country')
    function = fields.Char('Job Position')
    title = fields.Many2one('res.partner.title')
    parent_company_id = fields.Many2one("res.partner", string="Parent company", domain=[("is_company", "=", True)])
    partner_name = fields.Char(
        string="Company Name",
        help="""The name of the company which would be created when appointment is confirmed
        Leave it empty if a contact is an individual""",
    )
    agree_terms = fields.Boolean(string="Agree on terms and conditions",)
    pricelist_id = fields.Many2one("product.pricelist", string="Pricelist",)

    def write(self, values):
        """
        Re-write to make sure that empty values are not written to many2one & date fields
        """
        for key, val in values.items():
            if val == "":
                values.update({key: None})
        return super(appointment_contact_info, self).write(values)

    def _return_partner_values(self, partner_mode=False):
        """
        The universal method to parse partner vals to contact info vals and vice versa
         1. If create mode, we always create partner (used for confirming reservation)
         2. Otherwise we always retrieve value for contact info (used for partner onchange method and for controllers)
           2.1. If partner exists, we always retrieve its values. Otherwise they are own values

        Args:
         * partner_mode - bool - for the case to preapre value for new partner
    
        Returns:
         * dict

        Extra info:
         * params: 
          ** param 1 - which object values we retrieve; param2 - from which object we try to retrieve
          ** "0" - relates to info object; "1" - relates to partтer object
         * Expected singleton
        """
        self.ensure_one()
        values = {}
        considered_object = self
        param1 = param2 = 0
        if partner_mode:
            # 1
            param1 = 1
        else:
            # 2
            partner_name = considered_object.partner_name
            parent_company_id = considered_object.parent_company_id
            if self.partner_id:
                # 2.1
                considered_object = self.partner_id
                param2 = 1
                parent_company_id = self.partner_id.parent_id
                partner_name = parent_company_id and parent_company_id.name or self.partner_id.company_name or False
                values.update({"existing_partner": True})
            values.update({
                "partner_name": partner_name,
                "parent_company_id": parent_company_id,
            })
        for info_field in self._contact_fields:
            if info_field[2] == "many2one":
                values.update({info_field[param1]: considered_object[info_field[param2]].id})
            else:
                values.update({info_field[param1]: considered_object[info_field[param2]]})
        return values

    def _return_appointment_values(self, pure_values=False, tosession=False):
        """
        The method to retrieve appointment values 
        Mainly designed for inheritance and for custom fields usage

        Args:
         * pure_values - bool - to have values NOT adapted to website forms
         * tosession whether values are needed for website session

        Returns:
         * dict

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        values = {
            "description": self.description,
            "pricelist_id": self.pricelist_id.id,
            "agree_terms": self.agree_terms,
        }
        return values

    def _return_custom_fields(self):
        """
        The method to return fields which should be mandatory fields (on website!)

        Mainly designed for inheritance and for custom fields usage

        Returns:
         * list of chars
         * list of chars
         * list of chars
         * list of chars

        Extra info:
         * Expected singleton
        """
        return [], [], [], []

    def _apapt_phone_number(self, ph_key="mobile"):
        """
        The method to adapth phone / mobile number
        
        Methods:
         * _format_phone_number

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        record = self.sudo()
        if record[ph_key]:
            checked_number = record._format_phone_number(record[ph_key], False)
            if checked_number != record[ph_key]:
                record[ph_key] = checked_number

    def _format_phone_number(self, phone_number, raise_exception=False):
        """
        The method to get the proper phone representation
        
        Args:
         * phone_number - char
         * raise_exception- bool

        Returns:
         * Char

        Extra info:
         * read is used to update cache
         * Expected singleton
        """
        self.ensure_one()
        try:
            if isinstance(self.id, int):
                self.read()
        except Exception as er:
            pass
        country = self.partner_id.country_id or self.country_id or None
        return phone_validation.phone_format(
            phone_number,
            country.code if country else None,
            country.phone_code if country else None,
            force_format='INTERNATIONAL',
            raise_exception=raise_exception,
        )

    @api.model
    def _check_existing_duplicates(self, email=False, mobile=False, phone=False, partner_id=False):
        """
        The method to check wether partners with the same email, phone or number exists

        Args:
         * char
         * char
         * char
         * res.partner object (this object defined partner)

        Returns:
         * False if not found
         * res.partner record otherwise
        """
        self = self.sudo()
        exist_partner_id = False
        duplicates_domain = []
        if email:
            duplicates_domain.append(("email", "=", email))
        if mobile:
            if duplicates_domain:
                duplicates_domain = ["|"] + duplicates_domain
            duplicates_domain.append(("mobile", "=", mobile))
        if phone:
            if duplicates_domain:
                duplicates_domain = ["|"] + duplicates_domain
            duplicates_domain.append(("phone", "=", phone))
        if duplicates_domain:
            duplicates_domain += [
                "|",
                    ("active", "=", False),
                    ("active", "=", True),
            ]
            if partner_id:
                duplicates_domain = [("id", "!=", partner_id.id)] + duplicates_domain
            exist_partner_id = self.sudo().env["res.partner"].search(duplicates_domain, limit=1)
        return exist_partner_id
