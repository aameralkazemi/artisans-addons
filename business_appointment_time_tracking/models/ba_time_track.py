#coding: utf-8

from odoo import _, api, fields, models


class ba_time_track(models.Model):
    """
    The model to register and keep real work done
    """
    _name = "ba.time.track"
    _description = "Appointment Time Track"
    _rec_name = "user_id"

    @api.depends("datetime_start", "datetime_end")
    def _compute_duration(self):
        """
        Compute method for duration
        """
        for track in self:
            duration = 0.0
            if track.datetime_start and track.datetime_end:
                duration = (track.datetime_end - track.datetime_start).total_seconds() / (60 * 60)
            track.duration = duration

    user_id = fields.Many2one("res.users", "Responsible", default=lambda self: self.env.user)
    datetime_start = fields.Datetime(string="Start Time", required=True)
    datetime_end = fields.Datetime(string="End Time")
    duration = fields.Float(string="Duration", compute=_compute_duration, store=True,)
    appointment_id = fields.Many2one("business.appointment", "Appointment", required=True)

    _sql_constraints = [
        ('dates_check', 'check (datetime_end>datetime_start)', _('End time should be after start time!')),
    ]
