/** @odoo-module **/

import relationalFields from "web.relational_fields";
import fieldRegistry from "web.field_registry";
import rpc from "web.rpc";

const FieldMany2ManyResource = relationalFields.FieldMany2ManyTags.extend({
    tag_template: "FieldMany2ManyTagResource",
    events: _.extend({}, relationalFields.FieldMany2ManyTags.prototype.events, {
        'click .all_ba_resources': '_onAnyResources',
    }),
    /**
     * Re-write to add the button "any"
    */
    async _onAnyResources(event) {
        event.preventDefault();
        event.stopPropagation();
        var recordData = this.recordData;
        var resourceIDS = recordData.resource_ids.res_ids;
        var resourceTypeID = recordData.resource_type_id.res_id;
        var context = this.record.getContext(this.recordParams);
        var resources = await rpc.query({
            model: "business.resource.type",
            method: "return_ba_resources",
            args: [[resourceTypeID], resourceIDS],
            contex: context,
        });
        if (resources) {this._setValue({operation: 'ADD_M2M', ids: resources})};                        
    },
});

fieldRegistry.add('resource_many2many', FieldMany2ManyResource);


export default FieldMany2ManyResource;

