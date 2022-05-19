/** @odoo-module **/

import ListController from "web.ListController"; 
import { _lt } from "web.core";
import rpc from "web.rpc";
import timeSlots from "@business_appointment/js/time_slots";

const BusinessAppointmentListController = ListController.extend({
    buttons_template: 'Ba.ListView.buttons',
    /**
     * Re-write to launch wizard instead of simple form view
    */
    _onCreateRecord: function (event) {
        if (event) {event.stopPropagation();}
        var record = this.model.get(this.handle, {raw: true});
        var context = record.context;
        this._doActionWizard(context, _lt('Schedule appointment'));
    },
    /**
     * The method to open wizard form
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

export default BusinessAppointmentListController;
