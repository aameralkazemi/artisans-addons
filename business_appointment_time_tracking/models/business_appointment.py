#coding: utf-8

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class business_appointment(models.Model):
    """
    Overwrite to add the feature of time trackign
    """
    _inherit = "business.appointment"

    @api.depends("time_track_ids.datetime_start", "time_track_ids.datetime_end")
    def _compute_work_started(self):
        """
        Compute method for work_started
        """
        for ba in self:
            work_id = ba._find_started_work()
            ba.work_started = work_id and True or False
            ba.total_real_duration = sum(ba.time_track_ids.mapped("duration"))

    time_track_ids = fields.One2many("ba.time.track", "appointment_id", string="Time Tracking")
    work_started = fields.Boolean(string="Work Started", compute=_compute_work_started, store=True)
    total_real_duration = fields.Float(string="Total Duration", compute=_compute_work_started, store=True)

    def action_start(self):
        """
        The method to start work for appointment

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        started_work = self._find_started_work()
        if started_work:
            raise UserError(_("The work has been already started"))
        else:
            started_work_id = self.env["ba.time.track"].create({
                "user_id": self.env.user.id,
                "datetime_start": fields.Datetime.now(),
                "appointment_id": self.id,
            })

    def action_finish(self):
        """
        The method to finish work for appointment

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        started_work = self._find_started_work()
        if not started_work:
            raise UserError(_("The work has been already started"))
        else:
            started_work.write({"datetime_end": fields.Datetime.now()})

    def _find_started_work(self):
        """
        The method to find started work

        Returns:
         * ba.time.track or False

        Extra info:
         * Expected singleton
        """
        started_work_ids = self.time_track_ids.filtered(lambda ba: ba.datetime_start and not ba.datetime_end)
        res = started_work_ids and started_work_ids[0] or False
        return res