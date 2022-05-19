/** @odoo-module **/

import fieldRegistry from "web.field_registry";
import AbstractField from "web.AbstractField";
import dialogs from "web.view_dialogs";
import rpc from "web.rpc";
import { qweb, _lt } from "web.core";
import slotsWidgetCore from "@business_appointment/js/slots_widget_core";

const SelectSlotWizard = dialogs.FormViewDialog.extend({
    /**
     *   Re-write to add new parameters
    */
    init: function (parent, options) {
        this.originalView = options.originalView;
        this._super.apply(this, arguments);
    },
    /**
     *  The method to close wizard and open a required view or reload based on context
    */        
    async closeCalc(res) { 
        var record = this.form_view.model.get(this.form_view.handle, {raw: true});
        if (record.context.noBAactionReload) {await this.originalView.reload();}
        else {await this.do_action(res);};
        this.destroy();
    },
});

const timeSlotsWidget = AbstractField.extend(slotsWidgetCore.SlotsWidgetCore, {
    className: 'o_field_time_slots',
    tagName: 'div',
    resetOnAnyFieldChange: true,
    supportedFieldTypes: ['char'],
    events: _.extend({}, AbstractField.prototype.events, slotsWidgetCore.SlotsWidgetCore.events, {}),
    /**
     *   Re-write to pass to widgets necessary params
    */
    init: function (parent, options) {
        this._super.apply(this, arguments);
        this.numberOfAppointments = 1;
        this.duration = 1;
        this.parentRenderer = parent;
        this.parentRenderer.chosenAppointments = [];
    },
    /**
     *   The method to retrieve context
    */
    _getBaContext: function() {return this.record.getContext(this.recordParams)},
    /**
     *   The method to invoke rpc
    */
    _baRpc: function(values) {return rpc.query(values);},
    /**
     *   The method to render time slots table
    */
    _render: function () {
        var template = this._reCalcSlots();
        return template
    },
    /**
     *   The method to find filters and retrieve values of those
    */
    _retrieveFilters: function() {
        var recordData = this.recordData;
        this.resourceIDS = recordData.resource_ids.res_ids;
        this.resourceTypeID = recordData.resource_type_id.res_id;
        this.dateStart = recordData.date_start;
        this.dateEnd = recordData.date_end;
        this.duration = recordData.duration;
        this.allocationType = recordData.allocation_type;
        this.serviceID = recordData.service_id.res_id;
        this.appointment_id = recordData.appointment_id.res_id;
        this.pricelist_id = recordData.pricelist_id.res_id;
        if (this.appointment_id) {this.numberOfAppointments = 1;}
        else {this.numberOfAppointments = recordData.number_of_appointments;};
        return  this.resourceTypeID && this.serviceID && (this.resourceIDS.length > 0 
                || this.allocationType == 'automatic')
    },
    /**
     *   The method to open 'finish reservation' composer
    */
    async _onFinish(event) {
        var context = this._getBaContext();
        context.default_pricelist_id = this.pricelist_id;
        var view_id = await this._rpc({
            model: "choose.appointment.customer",
            method: "action_return_choose_wizard",
            args: [],
            context: context,
        });
        var dialog = new ChooseAppointmentCustomer(this, {
            res_model: "choose.appointment.customer",
            title: _lt("Choose Contact and Confirm"),
            view_id: view_id,
            readonly: false,
            shouldSaveLocally: false,
            context: context,
            timeSlotsWidget: this,
            size: "large",
            buttons: [
                {
                    text: (_lt("Confirm")),
                    classes: "btn-primary o_form_button_save",
                    click: function () {dialog._save()},
                },
                {
                    text: (_lt("Cancel")),
                    classes: "oe_link",
                    special: "cancel",
                    close: true,
                },
            ],
        }).open();
    },
    /**
     *   The method to show alert
    */
    _showWarning: function(title, message) {this.do_warn(title, message);},
    /**
     *   The method to unlink ALL not finished pre-reservations
    */
    destroy: function() {
        var context = this._getBaContext();
        var chosenAppointments = this.parentRenderer.chosenAppointments;
        if (chosenAppointments && chosenAppointments.length > 0) {
            var self = this;
            var toUnreserve = [];
            _.each(chosenAppointments, function (appointment) {
                toUnreserve.push(appointment.requestID)
                if (toUnreserve.length == chosenAppointments.length) {
                    self._rpc({
                        model: "business.appointment.core",
                        method: "write",
                        args: [toUnreserve, {"state": "processed"}],
                        context: context,
                    });
                };
            });
        };
        this._super.apply(this, arguments);
    },
});

const ChooseAppointmentCustomer = dialogs.FormViewDialog.extend({
    /**
     *   Re-write to add new params
    */
    init: function (parent, options) {
        this.timeSlotsWidget = options.timeSlotsWidget;
        this.parentRenderer = this.timeSlotsWidget.parentRenderer;
        this.topWindow = this.parentRenderer.__parentedParent.__parentedParent;
        this.topWindow.$el.addClass("hidden_appointment");
        this._super.apply(this, arguments);
    },
    /**
     *   Re-write to update main wizard
    */
    destroy: function() {
        this._super.apply(this, arguments);
        this.topWindow.$el.removeClass("hidden_appointment");
        this.timeSlotsWidget._reCalcSlots();
    },
    /**
     *   Re-write to make chosen appointments + close parent dialog + open form view
    */
    _save: function () {
        var self = this;
        self.form_view.saveRecord(self.form_view.handle, {
            stayInEdit: true,
            reload: false,
            savePoint: self.shouldSaveLocally,
            viewType: 'form',
        }).then(function (changedFields) {
            var record =  self.form_view.model.get(self.form_view.handle, {raw: true})
            var chosenAppointments = self.parentRenderer.chosenAppointments;
            self._rpc({
                model: "choose.appointment.customer",
                method: "action_finish_scheduling",
                args: [{"data": record.data, "chosen": chosenAppointments}],
                context: record.context,
            }).then(function (res) {
                self.close();
                self.topWindow.closeCalc(res);
            });

        });
    },
});

const timeSlotsWidgetShort = AbstractField.extend({
    className: 'o_field_time_slots',
    tagName: 'div',
    resetOnAnyFieldChange: false,
    supportedFieldTypes: ['char'],
    events: _.extend({}, AbstractField.prototype.events, {'click .remove_chosen': '_onRemoveSlot'}),
    /**
     *   Re-write to pass to widgets necessary params
    */
    init: function (parent, options) {
        this._super.apply(this, arguments);
        this.topWindow = parent.__parentedParent.__parentedParent;
        this.parentRenderer = this.topWindow.parentRenderer;
    },
    /**
     *   Re-write to render chosen time slots
    */
    _render: function () {
        var template = qweb.render('TimeSlotsTableShort', {"chosenAppointments": this.parentRenderer.chosenAppointments});
        this.$el.html(template);
        return template
    },
    /**
     *   The method to remove slot and make related pre-reservation as processed
    */
    async _onRemoveSlot(event) {
        event.preventDefault();
        event.stopPropagation();
        var slot = event.currentTarget.id;
        var preReservation = this.parentRenderer.chosenAppointments[slot].requestID;
        var context = this.record.getContext(this.recordParams)
        var actionRes = await this._rpc({
            model: "business.appointment.core",
            method: "write",
            args: [[preReservation], {"state": "processed"}],
            context: context,
        });
        var thisChosenAppointments = await slotsWidgetCore.spliceArray(this.parentRenderer.chosenAppointments, slot);
        this.parentRenderer.chosenAppointments = thisChosenAppointments;
        if (this.parentRenderer.chosenAppointments.length == 0) {if (this.topWindow) {this.topWindow.close()}}
        else {this._render()};
    },
});

fieldRegistry.add('timeSlotsWidget', timeSlotsWidget);
fieldRegistry.add('timeSlotsWidgetShort', timeSlotsWidgetShort);

export default {
    SelectSlotWizard: SelectSlotWizard,
    timeSlotsWidget: timeSlotsWidget,
    timeSlotsWidgetShort: timeSlotsWidgetShort,
    ChooseAppointmentCustomer: ChooseAppointmentCustomer,
}
