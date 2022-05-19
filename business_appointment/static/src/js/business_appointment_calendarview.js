/** @odoo-module **/

import BusinessAppointmentCalendarController from "@business_appointment/js/business_appointment_calendarcontroller";
import BusinessAppointmentCalendarRenderer from "@business_appointment/js/business_appointment_calendarrenderer";
import BusinessAppointmentCalendarModel from "@business_appointment/js/business_appointment_calendarmodel";
import CalendarView from "web.CalendarView";
import viewRegistry from "web.view_registry";
import { _lt } from "web.core";

const BusinessAppointmentCalendarView = CalendarView.extend({
    config: _.extend({}, CalendarView.prototype.config, {
        Controller: BusinessAppointmentCalendarController,
        Model: BusinessAppointmentCalendarModel,
        Renderer: BusinessAppointmentCalendarRenderer,
    }),
    icon: 'fa-clock-o',
    display_name: _lt('Appointments'),
    viewType: 'appointment_calendar',
});

viewRegistry.add('appointment_calendar', BusinessAppointmentCalendarView);

export default BusinessAppointmentCalendarView;
