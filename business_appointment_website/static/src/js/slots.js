/** @odoo-module **/

import rpc from "web.rpc";
import { qweb, _lt } from "web.core";
import Widget from "web.Widget";
import publicWidget from "web.public.widget";
import slotsWidgetCore from "@business_appointment/js/slots_widget_core";

var existingTimer = false;
/**
 * Copied from field_utils since can not be imported to website
*/
function parseFloatTime(value) {
    var factor = 1;
    if (value[0] === '-') {
        value = value.slice(1);
        factor = -1;
    }
    var float_time_pair = value.split(":");
    if (float_time_pair.length !== 2)
        return factor * parseFloat(value);
    var hours = parseInt(float_time_pair[0]);
    var minutes = parseInt(float_time_pair[1]);
    return factor * (hours + (minutes / 60));
};
/**
 * Copied from field_utils since can not be imported to website
*/
function formatFloatTime(value) {
    var pattern = '%02d:%02d';
    if (value < 0) {
        value = Math.abs(value);
        pattern = '-' + pattern;
    }
    var hour = Math.floor(value);
    var min = Math.round((value % 1) * 60);
    if (min === 60){
        min = 0;
        hour = hour + 1;
    }
    return _.str.sprintf(pattern, hour, min);
};
/**
 * The method to apply service-related restrictions: min, max, multiple
*/
function applyServiceRestrictions(duration) {
    var resDuration = duration,
        minDuration = parseFloat($(".ba_appointments_duration_min")[0].id),
        maxDuration = parseFloat($(".ba_appointments_duration_max")[0].id),
        multiplier = parseFloat($(".ba_appointments_duration_multiplier")[0].id); 
    if (!duration) {
        duration = minDuration;
        resDuration = duration;
    }   
    var residual = duration % multiplier;
    if (residual != 0) {resDuration = duration - residual + multiplier;};
    if (duration < minDuration) {resDuration = minDuration;}
    else if (duration > maxDuration) {resDuration = maxDuration};
    return resDuration
};
/**
 * The method to conver seconds to time duration format
*/
function returnTimeString(second_interval) {
    var finalTime = "";
    var days = Math.floor(second_interval / (3600*24))
    if (days != 0) {finalTime += days + _lt("d ")}
    var hours = Math.floor(second_interval % (3600*24) / 3600);
    if (days != 0 || hours != 0) {finalTime += hours + _lt("h ")}
    var mins = Math.floor(second_interval % 3600 / 60);
    if (days != 0 || hours !=0 || mins != 0) {finalTime += mins + _lt("m ")}
    finalTime += Math.floor(second_interval % 60) + _lt("s ");   
    return finalTime;     
};
/**
 * The method to re-organize visible parts of the timer to be expired
*/
function makeTimerExpired() {
    $('.normal_prereserv').addClass("ba_hidden");
    $('.expired_prereserv').removeClass("ba_hidden");
    $('.prereservation_div').removeClass("alert-info").addClass("alert-danger");
};
/**
 * The method to re-organize visible parts of the timer to be okay
*/
function makeTimeNormal() {
    $('.normal_prereserv').removeClass("ba_hidden");
    $('.expired_prereserv').addClass("ba_hidden");
    $('.prereservation_div').removeClass("alert-danger").addClass("alert-info");
};
/**
 * The method to launch pre-reservation timer
*/
function launchPreTimeer(leftPreTime, preTimer) {
    var timeAlert = $("#prereservation_timer_alert");
    if (existingTimer) {clearInterval(existingTimer);};
    if (!leftPreTime || leftPreTime == 0) {timeAlert.addClass("ba_hidden");}
    else {
        if (leftPreTime > 0) {
            makeTimeNormal();
            existingTimer = setInterval(function () {
                preTimer[0].innerHTML = returnTimeString(leftPreTime);
                if (leftPreTime <= 0) {
                    makeTimerExpired();
                    clearInterval(existingTimer);
                    // to get to the proper stage
                    var reloadPage = function() {
                        window.location.reload();
                    };
                    setTimeout(reloadPage, 5000);
                    preTimer[0].id = "-1";
                };
                leftPreTime -= 1;
            }, 1000)
        }
        else {
            makeTimerExpired();
        };
        timeAlert.removeClass("ba_hidden");
    };
};
/**
 * Time Slots Widget
*/
var timeSlotsWidget = Widget.extend(slotsWidgetCore.SlotsWidgetCore, {
    xmlDependencies: ['/business_appointment/static/src/xml/time_slots.xml'],
    events: _.extend({}, Widget.prototype.events, slotsWidgetCore.SlotsWidgetCore.events, {}),
    /**
     * Re-write to pass to widgets necessary params
    */
    init: function (parent) {
        this._super.apply(this, arguments);
        this.numberOfAppointments = 1;
        this.duration = 1;
        this.resourceTypeID = parseInt($(".ba_chosen_type")[0].id); 
        this.resourceIDS = eval($(".ba_chosen_resources")[0].id);  
        this.serviceID = parseInt($(".ba_chosen_service")[0].id);
        this.durationUom = $(".ba_appointments_duration_uom")[0].id;
        this.choices = $(".ba_appointments_choices")[0].id;
        this.pricelist_id = parseInt($(".ba_pricelist")[0].id);
        if (this.choices && this.durationUom == "hours") {
            _.each($(".choicable_time"), function (choice) {
                choice.innerHTML = formatFloatTime(choice.getAttribute("value"));
            });
        };
        this.parentRenderer = this; // hack for compatibility issues
        this.parentRenderer.chosenAppointments = eval($(".ba_prechosen_appointments")[0].id);
        var reScheduleEl = $(".re_schedule_appoin_ba");
        if (reScheduleEl && reScheduleEl.length != 0) {this.appointment_id = parseInt(reScheduleEl[0].id);}    
        else {this.appointment_id = false;};      
        if (this.appointment_id) {this.numberOfAppointments = 1;} // in case of re-schedule
        else {this.numberOfAppointments = parseInt($(".ba_appointments_number")[0].id);};
    },
    /**
     * The method to retrieve context
    */
    _getBaContext: function() {return {}},
    /**
     * Re-write to render slots insted of simple template rendering
    */
    renderElement: function () {
        this._replaceElement("<div/>");
        this._reCalcSlots();
    },
    /**
     * The method to find filters and retrieve values of those
    */
    _retrieveFilters: function() {
        this.dateEnd = $("#date_end")[0].value;
        this.dateStart = $("#date_start")[0].value;
        if (this.choices == "1") {
            var choiceObject = $("#duration_choice")[0];
            var newDuration = parseFloat(choiceObject.options[choiceObject.selectedIndex].getAttribute("value"));
            if (this.durationUom == "days") {
                newDuration = newDuration * 24;
            }
            this.duration = newDuration;
        }
        else if (this.durationUom == "hours") {this.duration = parseFloatTime($("#duration")[0].value)}
        else {this.duration = parseFloat($("#duration_days")[0].value) * 24};
        return true;
    },
    /**
     * The method to invoke rpc
    */
    _baRpc: function(values) {
        return rpc.query({
            route: "/appointments/update_json",
            params: {
                model: values.model,
                method: values.method,
                args: values.args,
            },
        });
    },
    /**
     * The method to get to the next stage from choosing slots
    */
    _onFinish: function(event) {
        window.location = "/appointments/5?progress_step=5";
    },
    /**
     * The method to show alert
    */
    _showWarning: function(title, message) {
        alert(title+"\n"+message);
    },
    /**
     * Re-write to trigger timer update if necessary  
     * Note: we should always make rpc, since in case even timer is not set, we check whether we should get back 
       from confirmation 
    */
    _resetPreTimer: function (unreserve, noreload) {
        var self = this; 
        var context = self._getBaContext();
        self._baRpc({
            model: "website.business.appointment",
            method: "return_prereservation_timer",
            args: [],
            context: context,
        }).then(function (res) {
            if (res !== false) {
                // we do not-recalc timer if a new slot is added - it is always bigger
                var timeAlert = $("#prereservation_timer_alert");
                if (timeAlert) {
                    var hiddenNow = timeAlert.hasClass("ba_hidden");
                    if ( (unreserve && !hiddenNow) || (!unreserve && hiddenNow) ) {
                        var preTimer = $('.prereservation_clock');
                        if (preTimer && preTimer.length > 0) {
                            launchPreTimeer(res, preTimer);
                        };
                    };
                };
            }
            else {
                // for the case we need to reload page
                if (!noreload) {
                    window.location = "/appointments/4?progress_step=4";
                };
            }
        });                    
            
    },
});
/**
 * Time slots contatiner for filters and slots
*/
publicWidget.registry.timeSlotsContainer = publicWidget.Widget.extend({
    selector: '#ba_slots_main_container',
    events: {
        "change #date_start": "_reCalcSlots",
        "change #date_end": "_reCalcSlots",
        "change #duration": "_onDurationChange",
        "change #duration_days": "_onDurationDaysChange",
        "change #duration_choice": "_reCalcSlots",
    },
    /**
     * Re-write to initiate time slots widget
    */
    start: function () {
        $("#duration")[0].value = formatFloatTime($("#duration")[0].getAttribute("value")); // since it is float initially
        this.slotsWidget = new timeSlotsWidget(); 
        this.slotsWidget.appendTo($('#ba_time_slots_widget')[0]);
    },
    /**
     * For each change > recalc slots
    */
    _reCalcSlots: function(event) {
        this.slotsWidget._reCalcSlots(); 
    },
    /**
     * when hours duration is changed
    */
    _onDurationChange: function(event) {
        var durationObj = $("#duration")[0];
        var duration = parseFloatTime(durationObj.value);  
        duration = applyServiceRestrictions(duration);
        durationObj.value = formatFloatTime(duration);
        this.slotsWidget._reCalcSlots();            
    },
    /**
     * when days duration is changed
    */
    _onDurationDaysChange: function(event) {
        var durationObjDay = $("#duration_days")[0];
        var duration = parseFloat(durationObjDay.value);  
        duration = applyServiceRestrictions(duration);
        durationObjDay.value = duration;
        this.slotsWidget._reCalcSlots();           
    },
});
/**
 * PreReservation Clock Timer
*/
publicWidget.registry.preservationClock = publicWidget.Widget.extend({
    selector: '#prereservation_timer_alert',
    start: function () {
        var preTimer = $(".prereservation_clock");
        launchPreTimeer(parseInt(preTimer[0].id), preTimer); 
    },
});
/**
 * Confirmation Clock Timer
*/
publicWidget.registry.resendTimer = publicWidget.Widget.extend({
    selector: '.resend_div',
    start: function () {
        var resendTimer = $(".resend_timer");
        var leftTime = parseInt(resendTimer[0].id) - 1;
        if (leftTime >= 0) {
            var resendInterval = setInterval(function () {
                resendTimer[0].innerHTML = leftTime + _lt(" seconds");
                if (leftTime <= 0) {
                    $('.resend_code').removeClass("ba_hidden");
                    $('.resend_div').addClass("ba_hidden");
                    clearInterval(resendInterval);
                }
                leftTime -= 1;
            }, 1000);
        }
        else {
            $('.resend_code').removeClass("ba_hidden");
            $('.resend_div').addClass("ba_hidden");
        };
    },
});
/**
 * Full details button on grid
*/
publicWidget.registry.baFullDetailsLink = publicWidget.Widget.extend({
    selector: '.ba_website_grid',
    events: {'click .ba_open_full_details': '_onOpenFullDetails',},
    _onOpenFullDetails: function (event) {
        event.preventDefault();
        event.stopPropagation();      
        var thishref = event.currentTarget.id; 
        window.open(thishref); 
    },
});
/**
 * Cancel re-schedulement process
*/
publicWidget.registry.rescheduleCancel = publicWidget.Widget.extend({
    selector: '.reschedule_div',
    events: {'click .remove_reschedule': '_onRemoveReschedulementBtn',},
    _onRemoveReschedulementBtn: function (event) {
        event.preventDefault();
        event.stopPropagation();
        rpc.query({
            route: "/my/business/appointments/cancel_reschedule",
            params: {},
        }).then(function (res) { 
            window.location.reload();  
        });  
    },
});
/**
 * Functional buttons on appointment page
*/
publicWidget.registry.baFunctionalButtons = publicWidget.Widget.extend({
    selector: '#ba_functional_buttons_div',
    events: {
        'click .repeat_ba_time': '_onRepeatBtn',
        'click .change_ba_time': '_onReScheduleBtn',
        'click .cancel_appointment': '_onCancelAppointment',
        'click .ba_suggest_complementaries': '_onChangeComplementaries',
    },
    /**
     * Repeat button
    */
    _onRepeatBtn: function (event) {
        event.preventDefault();
        event.stopPropagation();
        var appointmentID = parseInt(event.currentTarget.id);
        rpc.query({
            route: "/my/business/appointments/reschedule",
            params: {
                appointment_id: appointmentID,
                should_be_cancelled: false,
            },
        }).then(function (res) {window.open("/appointments/4")});      
    },   
    /**
     * Reschedule button
    */
    _onReScheduleBtn: function (event) {
        event.preventDefault();
        event.stopPropagation();
        var appointmentID = parseInt(event.currentTarget.id);
        rpc.query({
            route: "/my/business/appointments/reschedule",
            params: {
                appointment_id: appointmentID,
                should_be_cancelled: true,
            },
        }).then(function (res) { window.open("/appointments/4")});           
    },    
    /**
     * Cancel button
    */
    _onCancelAppointment: function(event) {
        event.preventDefault();
        event.stopPropagation();
        var isConfirmed = confirm(_lt("Are you sure you want to cancel this appointment?"))
        if (isConfirmed) {
            var appointmentID = parseInt(event.currentTarget.id);
            rpc.query({
                model: "business.appointment",
                method: "action_portal_cancel_reservation",
                args: [[appointmentID]],
            }).then(function (res) { window.location.reload()}); 
        };  
    },
    /**
     * Button to open suggested products
    */
    _onChangeComplementaries: function(event) {
        event.preventDefault();
        event.stopPropagation();
        var appointmentID = parseInt(event.currentTarget.id);
        rpc.query({
            route: "/my/business/appointments/complementaries",
            params: {
                appointment_id: appointmentID,
            },
        }).then(function (res) { 
            var suggested_products = res.suggested_products,
                existing_lines = res.existing_lines,
                ba_cur_pricelist_id = res.pricelist_id;
            var suggestedDialogDone = $.Deferred();
            if (suggested_products) {
                var suggestedDialogInstance = new suggestedWebsiteDialog(
                    self, 
                    {
                        "suggested_products": suggested_products, 
                        "suggestedDialogDone": suggestedDialogDone,
                        "existing_lines": existing_lines,
                        "pricelist_id": ba_cur_pricelist_id,
                    }
                );
                suggestedDialogInstance.open();
            }
            else {
                suggestedDialogDone.resolve()
            }
            suggestedDialogDone.then(function (suggested_products_vals) {
                if (suggested_products_vals === undefined) {window.location.reload()}
                else {
                    rpc.query({
                        route: "/my/business/appointments/update_extras",
                        params: {
                            appointment_id: appointmentID,
                            values: suggested_products_vals,
                        },
                    }).then(function (res) {window.location.reload()});
                }                            
            });
        });  
    },
});
/**
 * Suggested products (complementaries) dialog
*/
var suggestedWebsiteDialog = slotsWidgetCore.suggestedDialog.extend({
    /**
     *  Re-write to use proper rpc query
    */
    _onChangeQuantity: function(event) {
        var curValue = parseInt(event.currentTarget.value);
        if (!curValue) {curValue = 0};
        event.currentTarget.value = curValue; //for the case of incorrect symbols
        var productID = event.currentTarget.id;
        this.res_vals[productID] = {"product_id": productID, "product_uom_qty": curValue};
        if (this.pricelist_id) {
            // Calculate price
            rpc.query({
                route: "/my/business/appointments/calculate_price",
                params: {
                    "product_id": parseInt(productID), 
                    "pricelist_id": parseInt(this.pricelist_id), 
                    "cur_value": curValue
                },
            }).then(function (res) {
                var templatePrice = qweb.render('product_price_ba_item', {"price": res});
                var priceSection = $(event.target).parent().parent().parent().find(".ba_price_column#" + productID);
                if (priceSection) {       
                    priceSection[0].innerHTML =  templatePrice;         
                };
            });
        };
    }, 
});
