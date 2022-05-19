/** @odoo-module **/

import FormController from "web.FormController"; 
import { _lt } from "web.core";
import rpc from "web.rpc";
import timeSlots from "@business_appointment/js/time_slots";

const BusinessAppointmentController = FormController.extend({
    events: _.extend({}, FormController.prototype.events, {'click .re_schedule_appointment': '_onRescheduleAppointment',}),
    /**
     * Re write to rename create button
    */
    renderButtons: function ($node) {
        var self = this;
        $.when(this._super.apply(this, arguments)).then(function () {
            var createButton = self.$buttons.find(".o_form_button_create");
            if (createButton && createButton.length != 0) {
                createButton[0].innerHTML = _lt("Schedule");
            };
        });
    },
    /**
     *  Re-write to open wizard instead of edit form
    */
    createRecord: function (parentID) {
        event.preventDefault();
        event.stopPropagation();
        var record = this.model.get(this.handle, {raw: true});
        var context = record.context;
        this._doActionWizard(context, _lt('Schedule appointment'));
    },
    /**
     *  The method to launch re-scheduling wizard
    */
    _onRescheduleAppointment: function(event) {
        event.preventDefault();
        event.stopPropagation();
        var record = this.model.get(this.handle, {raw: true});
        var context = record.context;
        context.default_appointment_id = record.res_id;
        context.noBAactionReload = true;
        this._doActionWizard(context, _lt('Re-schedule / Re-assign appointment'));
    },
    /**
     *  he method to open wizard form
    */
    async _doActionWizard(globalContext, wizard_title) {
        var view_id = await rpc.query({
            model: "make.business.appointment",
            method: "action_return_wizard",
            args: [],
            context: globalContext,
        });
        var dialog = new timeSlots.SelectSlotWizard(this, {
            res_model: "make.business.appointment",
            title: wizard_title,
            view_id: view_id,
            readonly: false,
            shouldSaveLocally: false,
            context: globalContext,
            originalView: this,
            size: "large",
            buttons: [
                {
                    text: (_lt("Cancel")),
                    classes: "oe_link",
                    special: "cancel",
                    close: true,
                },
            ],
        }).open();
        this.reload();
    },
});

export default BusinessAppointmentController;
