/** @odoo-module **/

import BusinessAppointmentListController from "@business_appointment/js/business_appointment_list_controller";
import ListView from "web.ListView";
import viewRegistry from "web.view_registry";
    
const BAOWNListView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {Controller: BusinessAppointmentListController,}),
});

viewRegistry.add('ba_own_list', BAOWNListView);

export default BAOWNListView;
