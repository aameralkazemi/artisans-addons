from odoo import api, models


class search_partner_fields(models.Model):
    _inherit = 'res.partner'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if not args:
            args = []
        if name:
            domain = ['|', '|','|', ('phone', operator, name),
                      ('mobile', operator, name), ('partnerCode', operator, name) , ('altName', operator, name)
                      ]
            partners = self.search(domain + args, limit=limit, )
            res = partners.name_get()
            if limit:
                limit_rest = limit - len(partners)
            else:
                limit_rest = limit
            if limit_rest or not limit:
                args += [('id', 'not in', partners.ids)]
                res += super().name_search(
                    name, args=args, operator=operator, limit=limit_rest)
            return res
        return super().name_search(
            name, args=args, operator=operator, limit=limit
        )
