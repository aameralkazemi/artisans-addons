#coding: utf-8

from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval

DURATION_ERROR = _("Min Duration should be less than Max Duration. Both should be positive")
DURATION_NEGATIVE_ERROR = _("Duration should be positive")
MULTIPLE_DURATION_ERROR = _("Multiple should positive and less than max")
ROUND_RULE_ERROR = _("Round rule should be positive")
ROUND_RULE_DAY_ERROR = _("Start time should be within 0:00 and 23:59")
MAXCHOICE = 20

def _round_for_multiplier(duration, multiple_duration, max=False):
    """
    The method to round for multiplier

    Args:
     * duration - float
     * multiple_duration - float

    Returns:
     * float
    """
    new_duration = duration
    residual = duration % multiple_duration
    if residual != 0:
        multiple_duration = not max and multiple_duration or 0
        new_duration = duration - residual + multiple_duration
    return new_duration

class appointment_product(models.Model):
    """
    Appointment Service
    """
    _name = "appointment.product"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin', 'image.mixin']
    _description = "Service"

    @api.depends("appointment_ids.service_id", "appointment_ids.state")
    def _compute_appointment_len(self):
        """
        Compute method for appointment_len & planned_appointment_len
        """
        for service in self:
            service.appointment_len = len(service.appointment_ids)
            service.planned_appointment_len = len(service.appointment_ids.filtered(lambda ap: ap.state == 'reserved'))

    @api.depends("rating_ids.rating", "rating_ids.parent_res_id")
    def _compute_rating_satisfaction(self):
        """
        Compute method for rating_satisfaction

        Methods:
         * _calculate_satisfaction_rate of rating.rating
        """
        for service in self:
            rate_final = -1
            if service.rating_ids:
                rate = self.env["rating.rating"]._calculate_satisfaction_rate(service)
                rate_final = rate[service.id]
            service.rating_satisfaction = rate_final

    @api.constrains("manual_duration", "duration_uom", "min_manual_duration", "max_manual_duration", 
                    "min_manual_duration_days", "max_manual_duration_days", "appointment_duration", 
                    "appointment_duration_days", "multiple_manual_duration",
                    "multiple_manual_duration_days", "start_round_rule", "start_round_rule_days")
    def constrains_durations(self):
        """
        Constrain method for duration and start settings
        """
        for record in self:
            if record.duration_uom == "hours":
                if record.appointment_duration <= 0:
                    raise ValidationError(DURATION_NEGATIVE_ERROR)
                if record.start_round_rule <= 0:
                    raise ValidationError(ROUND_RULE_ERROR)
                if record.manual_duration:
                    if record.min_manual_duration <= 0 or record.min_manual_duration > record.max_manual_duration:
                        raise ValidationError(DURATION_ERROR)
                    if record.multiple_manual_duration <= 0 \
                            or record.multiple_manual_duration > record.max_manual_duration:
                        raise ValidationError(MULTIPLE_DURATION_ERROR)
            else:
                if record.appointment_duration_days <= 0:
                    raise ValidationError(DURATION_NEGATIVE_ERROR)
                if record.start_round_rule_days < 0 or record.start_round_rule_days >= 24:
                    raise ValidationError(ROUND_RULE_DAY_ERROR)
                if record.manual_duration:
                    if record.min_manual_duration_days <= 0 \
                            or record.min_manual_duration_days > record.max_manual_duration_days:
                        raise ValidationError(DURATION_ERROR)
                    if record.multiple_manual_duration_days <= 0 \
                            or record.multiple_manual_duration_days > record.max_manual_duration_days:
                        raise ValidationError(MULTIPLE_DURATION_ERROR)

    name = fields.Char(string="Service Name", translate=True)
    product_id = fields.Many2one("product.product", string="Related Product", required=True)
    duration_uom = fields.Selection(
        [("hours", "hours"), ("days", "days"),],
        string="Duration UoM",
        default="hours",
        help="""Define whether appointments should be scheduled for hours or for days. In the latter case make sure work
        times allow 24-hours periods (should start at 00:00 and end at 24:00)"""
    )
    appointment_duration = fields.Float(
        string="Appointment Default Duration",
        default=1.0,
        help="If not stated, the duration would be considered an one",
    )
    appointment_duration_days = fields.Integer(
        string="Duration of Appointment",
        default=1.0,
        help="If not stated, the duration would be considered an one",
    )
    appointment_ids = fields.One2many(
        "business.appointment",
        "service_id",
        string="Appointments",
    )
    ba_description = fields.Text(string="Appointment Description", translate=True,)
    manual_duration = fields.Boolean(
        string="Allow Manual Duration",
        help="Allow users to define appointment duration. Otherwise, it would be always default",
    )
    min_manual_duration = fields.Float(string="Min Duration Hours", default=0.5)
    max_manual_duration = fields.Float(string="Max Duration Hours", default=2,)
    multiple_manual_duration = fields.Float(
        string="Multiple for Hours",
        default=0.5,
        help="How manual duration should be rounded. E.g. 0:15 means rounding for 15 minutes: 0:17 > 0:30",
    )
    min_manual_duration_days = fields.Integer(string="Min Duration Days", default=1)
    max_manual_duration_days = fields.Integer(string="Max Duration Days", default=1)
    multiple_manual_duration_days = fields.Integer(
        string="Multiple for Days",
        default=1,
        help="How manual duration should be rounded. E.g. 2 means rounding for 2 days: 3 > 4",
    )    
    start_round_rule = fields.Float(
        string="Start Round",
        default=0.5,        
        help="""
            Define how appointment start time should be rounded. E.g. appointments are available now from 14:12 
            tomorrow. Then:
             * 0:05 - rounding for 5 minutes - would round start to 14:15
             * 0:10 - rounding for 10 minutes - would round start to 14:20
             * 0:30 - rounding for 30 minutes - would round start to 14:30
             * 1:00 - rounding for an hour - would round start to 15:00
             * 02:00 - rounding for 2 hours - would round start to 16:00
             * 24:00 - rounding for a day - would round start to 00:00
             * 32:00 - rounding for a day and 8 hours - would round to 08:00 the next day
            Take into account: ROUNDING IS DONE IN WORKING CALENDAR TIMEZONE
        """,
    )
    start_round_rule_days = fields.Float(
        string="Start Time",
        help="At which time daily services should start (defined in working calendar time zone)"
    )
    extra_working_calendar_id = fields.Many2one(
        "resource.calendar",
        string="Extra Calendar Restriction",
        help=""""If defined, this service would be available only in intervals that simultaneously suit this calendar
        and appointment resource calendar""",
    )
    location = fields.Char(string="Location", translate=True)  
    color = fields.Integer(string='Color')
    suggested_product_ids = fields.Many2many(
        "product.product",
        "product_product_appointment_product_ba_rel_table",
        "product_product_id",
        "appointment_product_id",
        string="Complementary Products",
        check_company=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.user.company_id,
        required=False,
    )
    appointment_ids = fields.One2many("business.appointment", "service_id", string="Appointments",)
    appointment_len = fields.Integer(
        string="Number of appointments",
        compute=_compute_appointment_len,
        store=True,
    )
    planned_appointment_len = fields.Integer(
        string="Planned appointments",
        compute=_compute_appointment_len,
        store=True,
    )
    rating_ids = fields.One2many(
        'rating.rating', 
        'service_id', 
        string='Ratings', 
        auto_join=True
    )
    rating_satisfaction = fields.Integer(
        string="Average Rating",
        compute=_compute_rating_satisfaction,
        store=True, 
        default=-1,
    )
    active = fields.Boolean(string="Active", default=True,)
    sequence = fields.Integer(string="Sequence")

    def _apply_service_restriction(self, duration):
        """
        The method to check duration min, max and multiple and re-calculate duration

        Args:
         * duration - float or ints

        Methods:
         * _return_min_max_duration
         * _round_for_multiplier

        Returns:
         * updated duration

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        min_duration, max_duration, multiple_duration = self._return_min_max_duration()
        new_duration = duration
        if duration < min_duration:
            new_duration = min_duration
        elif duration > max_duration:
            new_duration = max_duration
        else:
            new_duration = _round_for_multiplier(new_duration, multiple_duration)
        return new_duration

    def _return_min_max_duration(self):
        """
        The method to return min, max and multiple duration

        Methods:
         * _round_for_multiplier

        Returns:
         * float, float, float

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        duration_uom = self.duration_uom
        multiple_duration = duration_uom == "hours" and self.multiple_manual_duration \
                            or self.multiple_manual_duration_days
        min_duration = duration_uom == "hours" and self.min_manual_duration or self.min_manual_duration_days
        max_duration = duration_uom == "hours" and self.max_manual_duration or self.max_manual_duration_days
        return _round_for_multiplier(min_duration, multiple_duration),\
               _round_for_multiplier(max_duration,multiple_duration, True), multiple_duration

    def _return_available_choices(self, min_duration, max_duration, multiple_duration, man_max=False):
        """
        The method to contruct all options for choices (if not too long)
        
        Args:
         * min_duration - float
         * max_duration - float
         * multiple_duration - float
         * man_max - in case number should be passed manually (for demo mainly)

        Methods:
         * _round_for_multiplier

        Returns:
         * list (of available option) or empty list       
        """
        choice = []
        max_number = man_max or MAXCHOICE
        if (max_duration - min_duration) // multiple_duration <= max_number:
            itera = _round_for_multiplier(min_duration, multiple_duration)
            while itera <= _round_for_multiplier(max_duration, multiple_duration, True):
                choice.append(itera)
                itera += multiple_duration
        return choice

    def get_suggested_products(self, appointment_id, force_suggested=False, even_existing_lines=False):
        """
        The method to calculated offered to this service products

        Args:
         * appointment_id - in case of re-scheduling
         * force_suggested - str/bool - if "web", we should not check the setting, since it has been already checked
                                        implemented for website check
                                        if no, results are always empty
                                        if False, we come from backend
         * even_existing_lines - bool - to the case when previously chosen lines should be shown even they are
                                        not inside suggested
        
        Returns:
         * dict 
          ** suggested_products - dict - product values or False if none
          ** existing_lines - dict of lines previously chosen

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        self = self.sudo()
        res = False
        existing_lines = {}
        if not force_suggested:
            ICPSudo = self.env['ir.config_parameter'].sudo()
            force_suggested = safe_eval(ICPSudo.get_param('ba_extra_products_backend', default='False'))
        elif force_suggested == "web":
            force_suggested = True
        else:
            force_suggested = False
        if force_suggested:
            product_ids = self.suggested_product_ids
            res = product_ids and product_ids.mapped(lambda product: {
                "id": product.id,
                "name": product.name,
                "image_small": product.image_128,
            }) or False
            existing_lines = {}
            if res and appointment_id:
                appointment = self.env["business.appointment"].browse(appointment_id)
                if appointment.exists():
                    for extra in appointment.extra_product_ids:
                        if even_existing_lines and extra.product_id not in product_ids:
                            res.append({
                                "id": extra.product_id.id,
                                "name": extra.product_id.name,
                                "image_small": extra.product_id.image_128,
                            })
                        existing_lines[extra.product_id.id] = extra.product_uom_qty
        return {
            "suggested_products": res, 
            "existing_lines": existing_lines,
        }

    @api.model
    def calculate_price(self, product_id, pricelist_id, qty=1):
        """
        The method to calculate price for this product

        Args:
         * product_id - int
         * pricelist_id
         * qty - int            

        Returns:
         * str
        """
        lang = self._context.get("lang") or self.env.user.lang
        self = self.sudo()
        lcl_ctx = self._context.copy()
        product = self.env["product.product"].browse(product_id)
        res = False
        if product.exists():
            pricelist = self.env['product.pricelist'].browse(pricelist_id)
            if pricelist.exists():
                lcl_ctx.update({"pricelist": pricelist.id, "quantity": qty or 1.00})
                price = product.with_context(lcl_ctx).price
                currency = pricelist.currency_id
                if currency:
                    symbol = currency.symbol
                    res = currency.position == "after" and "{}{}".format(price, symbol) \
                                 or u"{}{}".format(symbol, price)
                    uom_name = product.uom_name
                    res = _(u"{} per {}".format(res, uom_name))
        return res
