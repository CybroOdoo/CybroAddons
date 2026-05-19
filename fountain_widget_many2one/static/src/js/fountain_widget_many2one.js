/** @odoo-module **/
import { Component, useEffect, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { FountainDropdown } from "./fountain_widget_component";
import { useService } from "@web/core/utils/hooks";

export class FountainWidget extends Component {
    static template = "FountainWidgetField";
    static components = {
        FountainDropdown,
    };
    setup() {
        this.orm = useService('orm');
        useEffect(() => { this.state.inputData = this.props.record.data[this.props.name] }, () => [this.props]);
        this.state = useState({
            childMenu: {},
            inputData: this.props.record.data[this.props.name],
            open: false // Control dropdown visibility
        });
        onWillStart(async () => {
            this.state.category = await this.orm.searchRead(this.props.record.fields.categ_id.relation, []);
        });
        this.index = 0; // Track the current depth of the dropdown

        // Bind the onClickDropDown method to ensure `this` refers to the component instance
        this.onClickDropDown = this.onClickDropDown.bind(this);
    }

    get inputData() {
        return {
            input: this.state.inputData ? this.state.inputData[1] : ''
        };
    }

    get parentMenu() {
        return this.state.category.filter(item => !item.parent_id);
    }

    get childKeys() {
        return Object.keys(this.state.childMenu);
    }

    onClickDropDown(parent_id, index = 0) {
        // Ensure index is a number, default to 0 if undefined
        index = Number(index) || 0;

        if (this.index >= index) {
            let childLength = this.childKeys.length;
            while (index < childLength) {
                const keyIndex = this.childKeys[index];
                delete this.state.childMenu[keyIndex];
                childLength--;
            }
        }
        let selectedCategory = this.state.category.find((item) => item.id === parent_id);
        let obj = this.state.category.filter(item => item.parent_id && item.parent_id[0] === parent_id);

        if (!this.state.childMenu.hasOwnProperty(parent_id) && obj.length > 0) {
            this.state.childMenu[parent_id] = obj;
            this.index = index + 1; // Increment index for nested levels
        }

        if (this.props.record && this.props.record.update) {
            this.state.inputData = [parent_id, selectedCategory.complete_name];
            this.props.record.update({ [this.props.name]: [parent_id, selectedCategory.complete_name] });
        } else {
            console.error('Update function not found in record props:', this.props);
        }
        this.state.open = false; // Close dropdown after selection
        return obj;
    }

    static props = {
        ...standardFieldProps,
        inputData: { type: Object, optional: true, default: {} },
    };
}

// Define the widget field with the correct structure
export const FountainWidgetField = {
    component: FountainWidget,
    supportedTypes: ["many2one"],
};

// Register the widget in the field registry
registry.category("fields").add("fountain_widget", FountainWidgetField);