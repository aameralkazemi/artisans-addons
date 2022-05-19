/** @odoo-module **/

import time from "web.time"; 
import Dialog from "web.Dialog";
import { qweb, _lt } from "web.core";

/**
 * The method to parse slot datetime to correct format
 * We do not use field_utils, since the latter is not available on the website
 * Here we assume that time is ALWAYS UTC
*/
function parseDateTime(value) {
    if (!value) {return false;}
    var datetime = moment.utc(value.replace(' ', 'T') + 'Z');
    if (datetime.isValid()) {
        if (datetime.year() === 0) {datetime.year(moment.utc().year())};
        if (datetime.year() >= 1900) {
            datetime.toJSON = function () {return this.clone().locale('en').format('YYYY-MM-DD HH:mm:ss')};
            return datetime;
        }
    }
    throw new Error(_.str.sprintf(_lt("'%s' is not a correct datetime"), value));
};
/**
 * The method to update chosen appointments when one is removed
*/
function spliceArray(chosenAppointments, slot) {
    var def = $.Deferred();
    var finalArray = [];
    _.each(chosenAppointments, function (choice) {
        if (choice.id < slot) {
            finalArray.push(choice);
        }
        else if (choice.id > slot) {
            var new_choice = choice;
            new_choice.id = choice.id - 1;
            finalArray.push(new_choice);
        }
        if (finalArray.length + 1 == chosenAppointments.length) {def.resolve(finalArray)};
    });
    return def;
};    
/**
 *  MixIn class to be used for web & website time slots widgets
*/
const SlotsWidgetCore = {
    events: {
        'change #select_tz': '_onChangeTZ',
        'click .timeslots_month_switcher': '_onChangeMonth',
        'change #select_year_switcher': '_onChangeYear',
        'click .timeslot_box': '_onAddSlot',    
        'click .remove_chosen': '_onRemoveSlot',
        'click .forward_checkout': '_onFinish',        
    },
    /**
     * The method to re-calculate slots based on changed timezone
    */
    _onChangeTZ: function(event) {
        event.preventDefault();
        event.stopPropagation();
        this.targetTZ = event.currentTarget.value;
        this._reCalcSlots();
    },
    /**
     * The method to calculate tz info to show slots
    */
    _getTzInfo: function(event) {
        var tzInfo = {};
        if (this.targetTZ) {tzInfo.targetTz = this.targetTZ;}
        else {
            tzInfo.timeZoneOffset = -(new Date().getTimezoneOffset());
            tzInfo.timeZoneName = Intl.DateTimeFormat().resolvedOptions().timeZone;
        };
        return tzInfo
    },
    /**
     * The method to adapt years / months based on retrieved slots
    */
    _amendSlotsperiods: function(res_slots) {
        res_slots.date_constructor = this._retrieveYearFromDate;               
        this.activeMonth = res_slots.active_month;
        if (res_slots.unique_years){
            if (!this.activeYear
                 || (this.activeYear && !res_slots.unique_years.includes(parseInt(this.activeYear)))
                ){this.activeYear = res_slots.unique_years[0];};}
        else {this.activeYear = false;}
        res_slots.activeYear = this.activeYear;            
        return res_slots
    },
    /**
     * The method to re-calculate slots when month is changed
    */
    _onChangeMonth: function(event) {
        event.preventDefault();
        event.stopPropagation();
        this.activeMonth = event.currentTarget.id;
        this._reCalcSlots();
    },
    /**
     * The method to show different months based on the year
    */
    _onChangeYear: function(event) {
        event.preventDefault();
        event.stopPropagation();
        var activeYear = event.currentTarget.value;
        this.activeYear = activeYear;
        var thisYearMonths = this.$el.find(".timeslots_month_switcher."+activeYear);
        if (thisYearMonths.length > 0) {thisYearMonths[0].click()};
    },
    /**
     * The method to update months based on selected year
    */
    _setUpActiveYear: function() {
        var activeYear = this.activeYear;
        var allMonths = this.$el.find(".timeslots_month_switcher");
        if (activeYear) {
            allMonths.addClass("hidden_appointment");
            var thisYearMonths = this.$el.find(".timeslots_month_switcher." + activeYear);
            thisYearMonths.removeClass("hidden_appointment");
        }
        else {allMonths.removeClass("hidden_appointment")};
    },
    /**
     * The method to convert date to a localized date
    */
    _retrieveYearFromDate: function(target_date, date_format) {
        var resDate = new Date(target_date);
        var res = target_date;
        if (date_format == "year") {res = resDate.getFullYear();}
        else if (date_format == "month") {res = moment.monthsShort()[resDate.getMonth()];}
        else if (date_format == "weekday") {res = moment.weekdaysShort()[resDate.getUTCDay()];}
        return res
    },
    /**
     * Dummy method to be inherited in case timer should be launched
    */
    _resetPreTimer: function(unreserve, noreload) {
        return 
    },
    /**
     * The method to call rpc and show available slots
    */
    async _reCalcSlots() {
        var def = $.Deferred();
        var needSlots = this._retrieveFilters();
        var context = this._getBaContext();
        var tzInfo = this._getTzInfo();
        var chosenAppointments = false;
        if (needSlots) {
            var res_slots = await this._baRpc({
                model: "business.resource",
                method: "action_construct_time_slots",
                args: [this.resourceIDS, this.resourceTypeID, this.serviceID, this.duration, this.dateStart, 
                       this.dateEnd, this.activeMonth, tzInfo, this.parentRenderer.chosenAppointments],
                context: context,
            });
            this._amendSlotsperiods(res_slots);
            if (res_slots.chosen_cores) {
                res_slots.chosenAppointments = res_slots.chosen_cores;
                this.parentRenderer.chosenAppointments = res_slots.chosen_cores;
            };
            var template = qweb.render('TimeSlotsTable', res_slots);
            this.$el.html(template);
            this._setUpActiveYear();
        }
        else {
            var template = qweb.render('TimeSlotsTable', {});
            this.$el.html(template);
        }
        return template
    },
    /**
     * The method to add slot to selected ones
    */
    async _onAddSlot(event) {
        event.preventDefault();
        event.stopPropagation();
        var self = this;
        var jsID = this.parentRenderer.chosenAppointments.length;
        if (this.numberOfAppointments != 1 && jsID+1 > this.numberOfAppointments) {
            this._showWarning(
                _lt('Maximum number of appointments'),
                _lt('Sorry, you can not schedule more appointments: the maximum number is reached'),
            );
        }
        else {
            var resourceIDS = $(event.target).data('id').toString().split(",");
            var start = event.currentTarget.id;
            var DateTimeStart = parseDateTime(start);
            var DateTimeEnd = moment(DateTimeStart);
            DateTimeEnd = DateTimeEnd.add(this.duration, 'hours');
            DateTimeEnd.toJSON = function () {return this.clone().locale('en').format('YYYY-MM-DD HH:mm:ss');};
            var title = event.currentTarget.title;
            var reservation_group_id = false;
            if (jsID != 0) {
                // we always try to fetch the first created appointment.
                // if it was removed, then we take from the next, and so on
                reservation_group_id = this.parentRenderer.chosenAppointments[0].requestID;
            };
            var appointmentVals = {
                "datetime_start": DateTimeStart,
                "datetime_end": DateTimeEnd,
                "service_id": this.serviceID,
                "resource_ids_list": resourceIDS,
                "tz": this._getTzInfo(), 
                "reservation_group_id": reservation_group_id
            };
            var context = this._getBaContext();
            var suggestedRes = await this._baRpc({
                model: "appointment.product",
                method: "get_suggested_products",
                args: [[this.serviceID], this.appointment_id],
                context: context,
            })
            var suggested_products = suggestedRes.suggested_products,
                existing_lines = suggestedRes.existing_lines;
            var suggestedDialogDone = $.Deferred();
            if (suggested_products) {
                var suggestedDialogInstance = new suggestedDialog(
                    this, 
                    {
                        "suggested_products": suggested_products, 
                        "suggestedDialogDone": suggestedDialogDone,
                        "existing_lines": existing_lines,
                        "pricelist_id": self.pricelist_id,
                    }
                );
                suggestedDialogInstance.open();
            }
            else {suggestedDialogDone.resolve()};
            
            suggestedDialogDone.then(function (suggested_products_vals) {
                if (suggested_products_vals) {
                    appointmentVals.extra_product_ids = suggested_products_vals;
                };
                self._baRpc({
                    model: "business.appointment.core",
                    method: "create_reservation",
                    args: [appointmentVals],
                    context: context,
                }).then(function (res) {
                    if (res) {
                        var def = $.Deferred();
                        if (self.numberOfAppointments == 1 && jsID != 0) {
                            self._unReserveSlot(self.parentRenderer.chosenAppointments[0].requestID, true).then(function (result) {
                                def.resolve();
                            });
                            self.parentRenderer.chosenAppointments = []
                            jsID = jsID - 1;
                        }
                        else {
                            def.resolve();
                        };
                        def.then(function() {
                            self.parentRenderer.chosenAppointments.push({
                                "requestID": res,
                                "id": jsID,
                            });
                            self._reCalcSlots().then(function () {
                                if (jsID+1 == self.numberOfAppointments) {
                                    self._onFinish();
                                }
                                else {
                                    self._resetPreTimer(false);
                                }
                            });
                        });
                    }
                    else {
                        // Mainly for the website. In background it would be UserError
                        self._showWarning(
                            _t('Sorry, this time slot has been just reserved'),
                            _t('Please try another one'),
                        );
                        self._reCalcSlots();
                    };
                });
            });
        };
    },
    /**
     * The method to remove slot and make related pre-reservation as processed
    */
    async _onRemoveSlot(event) {
        event.preventDefault();
        event.stopPropagation();
        var slot = event.currentTarget.id;
        var preReservation = this.parentRenderer.chosenAppointments[slot].requestID;
        await this._unReserveSlot(preReservation);
        var chosenRes = await spliceArray(this.parentRenderer.chosenAppointments, slot)
        this.parentRenderer.chosenAppointments = chosenRes;
        this._reCalcSlots();
    },
    /**
     * The method to delete prereservation
    */
    async _unReserveSlot(preReservation, noreload) {
        var context = this._getBaContext();
        var res = await this._baRpc({
            model: "business.appointment.core",
            method: "write",
            args: [[preReservation], {"state": "processed"}],
            context: context,
        });
        this._resetPreTimer(true, noreload);
        return res
    }
};

var suggestedDialog = Dialog.extend({
    xmlDependencies: (Dialog.prototype.xmlDependencies || [])
        .concat(['/business_appointment/static/src/xml/time_slots.xml']),
    template: 'suggested_products_dialog',
    events: _.extend({}, Dialog.prototype.events, {
        'click .remove_ba_pr_item': '_removeProductItem',
        'click .add_ba_pr_item': '_addProductItem',
        'change .ba_js_quantity': '_onChangeQuantity',
    }), 
    /**
     * Re-write to pass values for suggested product lines
    */
    init: function (parent, options) {
        this.suggestedDialogDone = options.suggestedDialogDone;
        this.suggested_products = options.suggested_products;
        this.existing_lines = options.existing_lines;
        this.pricelist_id = options.pricelist_id;
        this.res_vals = {};
        this.product_vals = undefined;
        this.parentWidget = parent;
        this._super(parent, _.extend({}, {
            title: _lt("Complementary Products"),
            buttons: [
                {text: options.save_text || _lt("Add"), classes: "o_save_button btn-primary", click: this.save},
                {text: "No Complementaries Needed", click: this.save_false}
            ]
        }, options || {}));
    },
    /**
     * Re-write to trigger existing values complete
    */
    start: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            var allQuantities = self.$(".ba_js_quantity");
            _.each(allQuantities, function (product_line) {
                if (self.existing_lines[product_line.id]) {
                    product_line.value = self.existing_lines[product_line.id];  
                };
            });
            allQuantities.change();                
        });
    },
    /**
     *  The method to remove product from the input
    */
    _removeProductItem: function(event) {this._manageNums(event, false)},
    /**
     *  The method to add product to the input
    */
    _addProductItem: function(event) {this._manageNums(event, true)},  
    /**
     *  The general method to manage add and reduce
    */
    _manageNums: function(event, plus_add) {
        event.preventDefault();
        event.stopPropagation();
        var inputQty = $(event.target).parent().parent().parent().find('.ba_js_quantity');
        var curValue = parseInt(inputQty[0].value);
        if (plus_add) {curValue = curValue + 1}
        else {curValue = curValue - 1};
        if (curValue < 0) {curValue = 0};
        inputQty[0].value = curValue;
        inputQty.change();
    },
    /**
     *  The method find the new quantity and update res_vals
    */
    _onChangeQuantity: function(event) { 
        var curValue = parseInt(event.currentTarget.value);
        if (!curValue) {curValue = 0};
        event.currentTarget.value = curValue; //for the case of incorrect symbols
        var productID = event.currentTarget.id;
        this.res_vals[productID] = {"product_id": productID, "product_uom_qty": curValue};
        if (this.pricelist_id) {
            // Calculate price
            this.parentWidget._baRpc({
                model: "appointment.product",
                method: "calculate_price",
                args: [parseInt(productID), parseInt(this.pricelist_id), curValue],
            }).then(function (res) {
                var templatePrice = qweb.render('product_price_ba_item', {"price": res});
                var priceSection = $(event.target).parent().parent().parent().find(".ba_price_column#" + productID);
                if (priceSection) {       
                    priceSection[0].innerHTML =  templatePrice;         
                };
            });
        };
    },   
    /**
     *  Re-write to save chosen suggested products
    */
    save: function (ev) {
        var self = this;
        var res_vals = [];
        var deferAll = $.Deferred();
        var itemsProcessed = 0;
        var totalNum = Object.keys(self.res_vals).length;
        if (totalNum === 0) {deferAll.resolve()};
        _.each(this.res_vals, function (product) {
            if (product.product_uom_qty > 0) {res_vals.push([0, 0, product])};
            itemsProcessed++;
            if (itemsProcessed === totalNum) {
              self.product_vals = res_vals;
              deferAll.resolve();
            };
        });
        deferAll.then(function () {
            self.close();                
        })
    },
    save_false: function(ev) {
        this.product_vals = false;
        this.close();
    },
    /**
     *  Re-write to indicate that selection is done and pass values to core
    */
    destroy: function (options) {
        this.suggestedDialogDone.resolve(this.product_vals);
        this._super.apply(this, arguments);
    },
});

export default {
    SlotsWidgetCore: SlotsWidgetCore,
    spliceArray: spliceArray,
    suggestedDialog: suggestedDialog,
}
