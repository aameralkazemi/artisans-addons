/** @odoo-module **/

import BusinessAppointmentController from "@business_appointment/js/business_appointment_formcontroller";
import FormView from "web.FormView";
import viewRegistry from "web.view_registry";

const BAOWNFormView = FormView.extend({
    config: _.extend({}, FormView.prototype.config, {Controller: BusinessAppointmentController,}),
});

viewRegistry.add('ba_own_form', BAOWNFormView);

export default BAOWNFormView;
