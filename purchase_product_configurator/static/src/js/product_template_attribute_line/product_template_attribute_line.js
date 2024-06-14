/** @odoo-module */

import { Component } from "@odoo/owl";
import { formatCurrency } from "@web/core/currency";

export class ProductTemplateAttributeLine extends Component {
    static template = "purchaseProductConfigurator.ptal";
    static props = {
        productTmplId: Number,
        id: Number,
        attribute: {
            type: Object,
            shape: {
                id: Number,
                name: String,
                display_type: {
                    type: String,
                    validate: type => ["color", "multi", "pills", "radio", "select"].includes(type),
                },
            },
        },
        attribute_values: {
            type: Array,
            element: {
                type: Object,
                shape: {
                    id: Number,
                    name: String,
                    html_color: [Boolean, String], // backend sends 'false' when there is no color
                    image: [Boolean, String], // backend sends 'false' when there is no image set
                    is_custom: Boolean,
                    excluded: { type: Boolean, optional: true },
                },
            },
        },
        selected_attribute_value_ids: { type: Array, element: Number },
        create_variant: {
            type: String,
            validate: type => ["always", "dynamic", "no_variant"].includes(type),
        },
        customValue: {type: [{value: false}, String], optional: true},
    };
    /**
     * Update the selected PTAV in the state.
     */
    updateSelectedPTAV(event) {
        this.env.updateProductTemplateSelectedPTAV(
            this.props.productTmplId, this.props.id, event.target.value, this.props.attribute.display_type == 'multi'
        );
    }

    /**
     * Update in the state the custom value of the selected PTAV.
     */
    updateCustomValue(event) {
        this.env.updatePTAVCustomValue(
            this.props.productTmplId, this.props.selected_attribute_value_ids[0], event.target.value
        );
    }
    /**
     * Return template name to use by checking the display type in the props.
     */
    getPTAVTemplate() {
        switch(this.props.attribute.display_type) {
            case 'color':
                return 'purchaseProductConfigurator.ptav-color';
            case 'multi':
                return 'purchaseProductConfigurator.ptav-multi';
            case 'pills':
                return 'purchaseProductConfigurator.ptav-pills';
            case 'radio':
                return 'purchaseProductConfigurator.ptav-radio';
            case 'select':
                return 'purchaseProductConfigurator.ptav-select';
        }
    }

    /**
     * Return the name of the PTAV
     */
    getPTAVSelectName(ptav) {
       return ptav.name;
    }

    /**
     * Check if the selected ptav is custom or not.
     */
    isSelectedPTAVCustom() {
        return this.props.attribute_values.find(
            ptav => this.props.selected_attribute_value_ids.includes(ptav.id)
        )?.is_custom;
    }
    
    /**
     * Check if the line has a custom ptav or not.
     */
    hasPTAVCustom() {
        return this.props.attribute_values.some(
            ptav => ptav.is_custom
        );
    }
 }
