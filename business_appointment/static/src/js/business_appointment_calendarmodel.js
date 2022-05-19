/** @odoo-module **/

import CalendarModel from "web.CalendarModel";
import rpc from "web.rpc";

function dateToServer (date) {return date.clone().utc().locale('en').format('YYYY-MM-DD HH:mm:ss')};

const BusinessAppointmentCalendarModel = CalendarModel.extend({
    /**
     * Re-write to add also resources domain
    */
    _getFilterDomain: function () {
        var domain = this._super.apply(this, arguments);
        if (this.activeResourceType) {
            domain.push(["resource_id.resource_type_id", "=", this.activeResourceType]);
        };
        if (this.activeResources && this.activeResources.length > 0) {
            domain.push(["resource_id", "in", this.activeResources]);
        };
        if (this.activeService) {domain.push(["service_id", "=", this.activeService])};
        if (this.activeStates && this.activeStates.length > 0) {domain.push(["state", "in", this.activeStates])};
        return domain;
    },
    /**
     * The method to make sure data is updated and check for write rights is done
    */
    reloadRecordData: function(record) {
        var def = $.Deferred();
        var self = this;
        var id = record.id;
        id = id && parseInt(id).toString() === id ? parseInt(id) : id;
        rpc.query({
            model: self.modelName,
            method: 'write',
            args: [[id], {}],
        }).then(function() {
            var data = _.omit(self.calendarEventToRecord(record), 'name');
            def.resolve(data);
        });
        return def
    },
});


export default BusinessAppointmentCalendarModel;
