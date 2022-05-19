#coding: utf-8

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class choose_appointment_customer(models.TransientModel):
    """
    The model to keep contact info required for appointment
    """
    _name = "choose.appointment.customer"
    _inherit = "appointment.contact.info"
    _description = "Finish Scheduling"
    _rec_name = "partner_id"

    @api.onchange("appointment_id")
    def _onchange_appointment_id(self):
        """
        Onchange method for appointment_id

        Methods:
         * _return_appointment_values

        Extra info:
         * Expected singleton
        """
        if self.appointment_id:
            values = self.appointment_id._return_appointment_values(True)
            values.update({"partner_id": self.appointment_id.partner_id.id,})
            return {"value": values}

    appointments = fields.Char(string="Tech Field")
    appointment_id = fields.Many2one("business.appointment", string="Appointment",)

    @api.model
    def action_return_choose_wizard(self):
        """
        The method to return for view id
        """
        return self.sudo().env.ref("business_appointment.choose_appointment_customert_form_view").id

    @api.model
    def action_finish_scheduling(self, args):
        """
        The method to make pre-reservation ready for confirmation

        Args:
         * dict of
          ** data - form view record data
          ** chosen - list of values for of appointment

        Methods:
         * write of business.appointment.core
         * action_start_prereserv() of business.appointment.core
         * _confirm_prereserv() of business.appointment.core
         * _return_action_appointments

        Returns:
         * ir.act.window dict

        Extra info:
         * in case of re-scheduling there migth only one pre-reservation --> so, we get the first
         * in case of internal pre-reservation we do not require confirmation, so we immediately approve pre-reservation
        """
        data = args.get("data")
        chosen = args.get("chosen")
        if not data or not chosen:
            raise UserError(_("Please select a contact and appointments"))
        appointment_ids = False
        if data.get("appointment_id"):
            appointment_ids = self.env["business.appointment"].browse(data.get("appointment_id"))
        if data.get("appointment_id") is not None:
            del data["appointment_id"]
        if data.get("appointments") is not None:
            del data["appointments"]
        if appointment_ids:
            pre_reservation_id = self.env["business.appointment.core"].browse(chosen[0].get("requestID"))
            pre_reservation_id.write(data)
            pre_reservation_id.action_start_prereserv()
            pre_reservation_id._confirm_prereserv(appointment_ids)
        else:
            appointment_ids = self.env["business.appointment"]
            for choice in chosen:
                pre_reservation_id = self.env["business.appointment.core"].browse(choice.get("requestID"))
                pre_reservation_id.write(data)
                pre_reservation_id.action_start_prereserv()
                appointment_ids += pre_reservation_id._confirm_prereserv()
        return self._return_action_appointments(appointment_ids)

    @api.model
    def _return_action_appointments(self, appointment_ids):
        """
        Method to return proper actions for those appointment_ids

        Args:
         * appointment_ids - business_appointment recordset

        Returns:
         * ir.act.window dict
        """
        res = False
        if len(appointment_ids) > 1:
            res = self.sudo().env.ref("business_appointment.business_appointment_action").read()[0]
        elif len(appointment_ids) == 1:
            res = self.sudo().env.ref("business_appointment.business_appointment_action_only_form").read()[0]
            res["res_id"] = appointment_ids.id
        return res
