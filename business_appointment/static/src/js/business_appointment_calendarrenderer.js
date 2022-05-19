/** @odoo-module **/

import CalendarRenderer from "web.CalendarRenderer";
import FieldManagerMixin from "web.FieldManagerMixin";
import Widget from "web.Widget";
import rpc from "web.rpc";
import { qweb } from "web.core";

/**
 *  Services filters (part of resource type sidebar)
*/
const ServicesSideBarFilter = Widget.extend(FieldManagerMixin, {
    template: 'BusinessAppointmentServicesFilters',
    events: _.extend({}, FieldManagerMixin.events, {
        "click .ba_service_check": "_onChangeService",
        "click .clear_services": "_onClearServices",
    }),
    /**
     * Re-write to pass to widgets necessary params
    */
    init: function (parent, options) {
        this._super.apply(this, arguments);
        FieldManagerMixin.init.call(this);
        this.availableServices = options.availableServices;
        this.resourceFilter = parent;
        this.activeService = parent.activeService;
        this.initial_context = options.initial_context;
    },
    /**
     * The method triggered when resource is changed
    */
    _onChangeService: function(event) {
        var serviceID = parseInt(event.currentTarget.id);
        if (serviceID != this.activeService) {
            this.activeService = serviceID;
            this.resourceFilter._triggerDomainupdate(serviceID);
            this.$el.find(".ba_service_check.ba_active_element").removeClass("ba_active_element");
            this.$el.find(".ba_service_check#"+event.currentTarget.id).addClass("ba_active_element");
        };
    },
    /**
     * The method to uncheck service
    */
    _onClearServices: function(event) {
        this.activeService = false;
        this.resourceFilter._triggerDomainupdate(false);
        this.$el.find(".ba_service_check.ba_active_element").removeClass("ba_active_element");
    },
    /**
     * Re-write to apply default service if passed in context
    */
    renderElement: function () {
        this._super.apply(this, arguments);
        var defaultService = false;
        if (this.initial_context) {
            if (this.initial_context.default_service_id) {
                defaultService = this.initial_context.default_service_id;
            }
            else if (this.initial_context.search_default_service_id) {
                defaultService = this.initial_context.search_default_service_id;
            }
        };
        if (defaultService) {this.$el.find(".ba_service_check#"+defaultService.toString()).click();};
        this.initial_context = false;
    },
});
/**
 *  Resources filters (part of resource type sidebar)
*/
const ResourceSideBarFilter = Widget.extend(FieldManagerMixin, {
    template: 'BusinessAppointmentResourcesFilters',
    events: _.extend({}, FieldManagerMixin.events, {
        "click .ba_resource_check": "_onChangeResource",
        "click .clear_resources": "_onClearResources",
        "click .all_resources": "_onChooseAllResources",
    }),
    /**
     * Re-write to pass to widgets necessary params
    */
    init: function (parent, options) {
        this._super.apply(this, arguments);
        FieldManagerMixin.init.call(this);
        this.availableResources = options.availableResources;
        this.resourceTypeServices = options.resourceTypeServices;
        this.activeResources = [];
        this.sidebar = parent;
        this.activeService = parent.activeService;
        this.initial_context = options.initial_context;
        this.getColor = options.getColor;
    },
    /**
     * Re-write to re-render resource type services
    */
    renderElement: function () {
        this._super.apply(this, arguments);
        var self = this;
        this._reRenderServices().then(function (activeService) {
            self._triggerDomainupdate(activeService);
            var defaultResources = [];
            if (self.initial_context) {
                if (self.initial_context.default_resource_id) {
                    defaultResources = [self.initial_context.default_resource_id];
                }
                else if (self.initial_context.search_default_resource_id) {
                    defaultResources = [self.initial_context.search_default_resource_id];
                }
                else if (self.initial_context.default_resource_ids) {
                    defaultResources = self.initial_context.default_resource_ids;
                };
            };
            if (defaultResources.length > 0) {
                _.each(defaultResources, function (defaultResource) {
                    self.$el.find(".ba_resource_check#"+defaultResource.toString()).click();
                });             
            };
            self.initial_context = false;
        });
    },
    /**
     * The method triggered when resource is changed
    */
    async _onChangeResource(event) {
        var resourceID = parseInt(event.currentTarget.id);
        var activeResource = $(event.currentTarget).hasClass("ba_resource_not_chosen");
        if (activeResource) {
            this.activeResources.push(resourceID);
            $(event.currentTarget).removeClass("ba_resource_not_chosen").addClass("ba_resource_chosen");
        }
        else {
            var removedIndex = this.activeResources.indexOf(resourceID);
            if (removedIndex > -1) {this.activeResources.splice(removedIndex, 1);};
            $(event.currentTarget).removeClass("ba_resource_chosen").addClass("ba_resource_not_chosen");
        }
        var activeService = await this._reRenderServices();
        this._triggerDomainupdate(activeService);
    },
    /**
     * The method to re-render available services based on chosen resources
    */
    _reRenderServices: function() {
        var self = this;
        var def = $.Deferred();
        self._findAvailableServices().then(function (availableServices) {
            self._deDuplicateServices(availableServices).then(function (res) {
                if (self.serviceWidget) {self.serviceWidget.destroy();};
                if (res.deduplicatedServices.length > 0) {
                    var options = {
                        "availableServices": res.deduplicatedServices,
                        "initial_context": self.initial_context,
                    };
                    var serviceFilters = new ServicesSideBarFilter(self, options);
                    var targetEl = self.$el.find(".services_append");
                    serviceFilters.appendTo(targetEl);
                    self.serviceWidget = serviceFilters;
                    def.resolve(res.activeService);
                }
                else {
                    self._triggerDomainupdate(false);
                };
            });
        });
        return def;
    },
    /**
     * The method to find available service according to active resources
    */
    _findAvailableServices: function () {
        var self = this;
        var def = $.Deferred();
        var activeResources = self.activeResources;
        if (!activeResources || activeResources.length == 0) {
            // If no resources are chosen
            def.resolve(self.resourceTypeServices);
        }
        else {
            // If there are active resources
            var availableResources = self.availableResources
            var availableServices = [];
            var itemsProcessed = 0;
            _.each(availableResources, function (resource) {
                if (activeResources.includes(resource.id)) {availableServices = availableServices.concat(resource.services);};
                itemsProcessed ++;
                if (itemsProcessed == availableResources.length) {def.resolve(availableServices)};
            });
        }
        return def;
    },
    /**
     * The method to remove repeated services
    */
    _deDuplicateServices: function(availableServices) {
        var self = this;
        var def = $.Deferred();
        var itemsProcesseded = 0;
        var deduplicatedServices = availableServices.concat();
        var activeService = false;
        if (availableServices.length > 0) {
            _.each(availableServices, function (service) {
                for(var j=itemsProcesseded+1; j<deduplicatedServices.length; ++j) {
                    if (service.id === deduplicatedServices[j].id) {deduplicatedServices.splice(j--, 1)};
                };
                if (self.activeService == service.id) {activeService = service.id};
                itemsProcesseded ++;
                if (itemsProcesseded == availableServices.length) {
                    def.resolve({
                        "deduplicatedServices": deduplicatedServices,
                        "activeService": activeService,
                    })
                };
            });
        }
        else {
            def.resolve({
                "deduplicatedServices": deduplicatedServices,
                "activeService": activeService,
            });
        }
        return def
    },
    _triggerDomainupdate: function(activeService) {
        this.sidebar._triggerDomainupdate(this.activeResources, activeService);
        this.activeService = activeService;
    },
    /**
     * The method to uncheck resources
    */
    async _onClearResources(event) {
        this.activeResources = [];
        var activeService = await this._reRenderServices();
        this._triggerDomainupdate(activeService);
        this.$el.find(".ba_resource_chosen.ba_element.ba_resource_check").removeClass("ba_resource_chosen").addClass("ba_resource_not_chosen");
    },
    /**
     * The method to check all resources
    */
    async _onChooseAllResources(event) {
        var self = this,
            activeResources = [],
            iterNum = 0,
            availableResources = this.availableResources;
        _.each(availableResources, function (resource) {
            activeResources.push(resource.id);
            iterNum ++;
            if (iterNum == availableResources.length) {
                self.activeResources = activeResources;
                var activeService = self._reRenderServices();
                self._triggerDomainupdate(activeService);
            }
        });
        this.$el.find(".ba_resource_not_chosen.ba_element.ba_resource_check").removeClass("ba_resource_not_chosen").addClass("ba_resource_chosen");
    },
});
/**
 *  Resource types sidebar
*/
const ResourceTypesSideBarFilter = Widget.extend(FieldManagerMixin, {
    template: 'BusinessAppointmentSideBarFilter',
    events: _.extend({}, FieldManagerMixin.events, {
        "click .ba_resource_type_check": "_onChangeResourceType",
        "click .ba_state_check": "_onChangeState",
        "click .clear_states": "_onClearStates",
        "click .all_states": "_onChooseAllStates",
        "click .save_default_choices": "_onSaveDefaults",
    }),
    /**
     * Re-write to pass to widgets necessary params
    */
    init: function (parent, options) {
        this._super.apply(this, arguments);
        FieldManagerMixin.init.call(this);
        this.availableResourceTypes = options.availableResourceTypes;
        this.availableStates = options.availableStates;
        this.activeStates = [];
        this.parentRender = parent;
        this.activeService = false;
        this.getColor = options.getColor;
        this.initial_context = options.initial_context;
    },
    /**
     * Re-write to simulate click on the first available resource type to render resources and click on state
    */
    renderElement: function () {
        this._super.apply(this, arguments);
        if (this.availableResourceTypes.length > 0) {
            var defaultResourceType = this.availableResourceTypes[0].id;
            var defaultStates = [];
            if (this.initial_context) {
                if (this.initial_context.default_resource_type_id) {
                    defaultResourceType = this.initial_context.default_resource_type_id;
                }
                else if (this.initial_context.search_default_resource_type_id) {
                    defaultResourceType = this.initial_context.search_default_resource_type_id;
                };
                if (this.initial_context.default_state) {
                    defaultStates = [this.initial_context.default_state];
                }
                else if (this.initial_context.search_default_state) {
                    defaultStates = [this.initial_context.search_default_state];
                }
                else if (this.initial_context.default_states) {
                    defaultStates = this.initial_context.default_states;
                };
            };
            var defaultResourceElements = this.$el.find(".ba_resource_type_check#"+defaultResourceType.toString());
            if (defaultResourceElements.length > 0) {defaultResourceElements[0].click();}
            else {this.$el.find(".ba_resource_type_check#"+this.availableResourceTypes[0].id).click();};
            if (defaultStates.length > 0) {
                var self = this;
                _.each(defaultStates, function (defaultState) {
                    self.$el.find(".ba_state_check#"+defaultState).click();
                });             
            }
            else {this.$el.find(".ba_state_check#reserved").click();};
            this.initial_context = false;
        };
    },
    /**
     * The method triggered when resource type is changed
    */
    _onChangeResourceType: function(event) {
        var resourceTypeID = parseInt(event.currentTarget.id);
        if (resourceTypeID != this.activeResourceType) {
            this.activeResourceType = resourceTypeID;
            this.$el.find(".ba_resource_type_check.ba_active_element").removeClass("ba_active_element");
            this.$el.find(".ba_resource_type_check#"+event.currentTarget.id).addClass("ba_active_element");
            this._reRenderResources();
        };
    },
    /**
     * The method to update view based on checked values
    */
    _reRenderResources: function() {
        var self = this;
        _.each(self.availableResourceTypes, function (resourceType) {
            if (self.activeResourceType == resourceType.id) {
                if (self.resourcesWidget) {self.resourcesWidget.destroy();}
                if (resourceType.resources.length > 0) {
                    var options = {
                        "availableResources": resourceType.resources,
                        "resourceTypeServices": resourceType.services,
                        "initial_context": self.initial_context,
                        "getColor": self.getColor,
                    }
                    var resourceFilters = new ResourceSideBarFilter(self, options);
                    var targetEl = self.$el.find(".ba_overall_filters");
                    resourceFilters.appendTo(targetEl);
                    self.resourcesWidget = resourceFilters;
                }
                else {self._triggerDomainupdate([], false)};
            };
        });
    },
    /**
     * The method triggered when resource is changed
    */
    _onChangeState: function(event) {
        var self = this;
        var stateValue = event.currentTarget.id;
        var activeState = $(event.currentTarget).hasClass("ba_resource_not_chosen");
        if (activeState) {
            this.activeStates.push(stateValue);
            $(event.currentTarget).removeClass("ba_resource_not_chosen").addClass("ba_resource_chosen");
        }
        else {
            var removedIndex = this.activeStates.indexOf(stateValue);
            if (removedIndex > -1) {this.activeStates.splice(removedIndex, 1);};
            $(event.currentTarget).removeClass("ba_resource_chosen").addClass("ba_resource_not_chosen");
        }
        this.parentRender.trigger_up('changeBaState', {"activeStates": this.activeStates});
    },
    /**
     * The method to trigger controller method to reload with updated domain
    */
    _triggerDomainupdate: function(activeResources, activeService) {
        var data = {"activeResourceType": this.activeResourceType,}
        if (activeResources) {data.activeResources = activeResources;}
        else {data.activeResources = []};
        data.activeService = activeService;
        this.activeService = activeService;
        this.activeResources = activeResources;
        this.parentRender.trigger_up('changeResourceType', data);
    },
    /**
     * The method to check all resources
    */
    _onChooseAllStates: function(event) {
        var self = this,
            activeStates = [],
            iterNum = 0,
            availableStates = this.availableStates;
        _.each(availableStates, function (state) {
            activeStates.push(state[0]);
            iterNum ++;
            if (iterNum == availableStates.length) {
                self.activeStates = activeStates;
                self.parentRender.trigger_up('changeBaState', {"activeStates": self.activeStates});
            }
        });
        this.$el.find(".ba_resource_not_chosen.ba_element.ba_state_check").removeClass("ba_resource_not_chosen").addClass("ba_resource_chosen");
    },
    /**
     * The method to uncheck states
    */
    _onClearStates(event) {
        this.activeStates = [];
        this.parentRender.trigger_up('changeBaState', {"activeStates": this.activeStates});
        this.$el.find(".ba_resource_chosen.ba_element.ba_state_check").removeClass("ba_resource_chosen").addClass("ba_resource_not_chosen");
    },
    /**
     * The method to find current selection and save those to the current user
    */
    _onSaveDefaults: function(event) {
        event.preventDefault();
        event.stopPropagation();
        var defaultValues = {
            "default_resource_type_id": this.activeResourceType,
            "default_resource_ids": this.activeResources,
            "default_service_id": this.activeService,
            "default_states": this.activeStates,
        };
        rpc.query({
            model: "res.partner",
            method: "save_ba_calendar_defaults",
            args: [defaultValues],
        });
    },
});
/**
 *  Calendar Renderer
*/
const BusinessAppointmentCalendarRenderer = CalendarRenderer.extend({
    /**
     * Re-write to declare new params
    */
    init: function () {
        this.alreadyExist = false;
        this._super.apply(this, arguments);
    },
    /**
     * Re-write to replace standard sidebar filters with ours
    */
    _renderFilters: function () {if (!this.alreadyExist) {this._renderResourcesTypes()}},
    /**
     * The method to render sidebar of resource types & misc
    */
    async _renderResourcesTypes() {
        var self = this;
        var context = this.state.context;
        var typesResources = await rpc.query({
            model: "business.resource.type",
            method: "return_types_and_resources",
            args: [[]],
            context: context,
        });
        var options = {
            "availableResourceTypes": typesResources.availableResourceTypes,
            "availableStates": typesResources.availableStates,
            "getColor": self.getColor.bind(self),
            "initial_context": typesResources.initial_context,
        }
        var resourceTypesFilters = new ResourceTypesSideBarFilter(this, options);
        this.alreadyExist = true;
        resourceTypesFilters.appendTo(this.$sidebar);

    },
});

export default BusinessAppointmentCalendarRenderer
