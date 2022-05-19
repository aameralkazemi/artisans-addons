/** @odoo-module **/

import CalendarController from "web.CalendarController"; 
import dialogs from "web.view_dialogs";
import { qweb, _lt } from "web.core";
import rpc from "web.rpc";
import timeSlots from "@business_appointment/js/time_slots";

const BusinessAppointmentCalendarController = CalendarController.extend({
    custom_events: _.extend({}, CalendarController.prototype.custom_events, {
        changeResourceType: '_onChageResourceDomain',
        changeBaState: '_onChageState',
    }),
    /**
     * Re-write to always open resource allocation wizard
    */
    _onOpenCreate: function (event) {
        var data = this.model.calendarEventToRecord(event.data);
        var context = _.extend({}, this.context, event.options && event.options.context);
        context.default_name = data.name || null;
        if (this.mapping.date_start && data[this.mapping.date_start]) {
            context['default_date_start'] = this.getTZOffsetDate(data[this.mapping.date_start])
        };
        if (this.mapping.date_stop && data[this.mapping.date_stop]) {
            context['default_date_end'] = this.getTZOffsetDate(data[this.mapping.date_stop])
        };
        if (this.model.activeResourceType) {context['default_resource_type_id'] = this.model.activeResourceType;};
        if (this.model.activeResources) {context['default_resource_ids'] =  this.model.activeResources;};
        if (this.model.activeService) {context['default_service_id'] = this.model.activeService;};
        if (context.default_date_start && context.default_date_end) {
            var defa_duration = Math.abs(context.default_date_end - context.default_date_start) / 36e5;
            if (defa_duration < 8) {context["defa_duration"] = defa_duration;}
        };
        this._doActionWizard(context, _lt('Schedule Appointment'));
    },
    /**
     * Re-write to launch re-scheduling instead of actual resize
    */
    _onUpdateRecord: function(event) {
        var self = this;
        this._resSchedule(event, true).then(function () {self.reload();});
    },
    /**
     * Re-write to launch re-scheduling instead of actual resize
    */
    _onDropRecord: function (event) {
        var self = this;
        this._resSchedule(event).then(function () {self.reload();});
    },
    /**
     * The method to calculate resources & services --> reload view
    */
    _onChageResourceDomain: function(event) {
        this.model.activeResourceType = event.data.activeResourceType;
        this.model.activeResources = event.data.activeResources;
        this.model.activeService = event.data.activeService;
        this.reload();
    },
    /**
     * The method to calculate resources & services --> reload view
    */
    _onChageState: function(event) {
        this.model.activeStates = event.data.activeStates;
        this.reload();
    },
    /**
     * The method to trigger resceduling wizard for this appointment
    */
    _resSchedule: function(event, delay) {
        var self = this;
        var def = $.Deferred();
        this.model.reloadRecordData(_.extend({}, event.data, {'drop': true,})).then(function (data) {
            var context = _.extend({}, self.context, event.options && event.options.context);
            if (self.mapping.date_start && data[self.mapping.date_start]) {
                context['default_date_start'] = self.getTZOffsetDate(data[self.mapping.date_start])
            };
            if (self.mapping.date_stop && data[self.mapping.date_stop]) {
                context['default_date_end'] = self.getTZOffsetDate(data[self.mapping.date_stop])
            };
            if (delay && context.default_date_start && context.default_date_end) {
                context["defa_duration"] = Math.abs(context.default_date_end - context.default_date_start) / 36e5;
            };
            var id = event.data.id;
            id = id && parseInt(id).toString() === id ? parseInt(id) : id;
            context["default_appointment_id"] = id;
            self._doActionWizard(context, _lt('Re-shedule / Re-assign appointment'));
            def.resolve();
        });
        return def
    },
    /**
     * The method to open wizard form
    */
    async _doActionWizard(globalContext, wizard_title) {
        globalContext.noBAactionReload = true;
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
    /**
     * The method to adapt date to timezone to make proper UTC defaults
    */
    getTZOffsetDate: function(date) {return date.add(this.getSession().getTZOffset(date), 'minutes')},
});


export default BusinessAppointmentCalendarController;
