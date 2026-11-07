/** @odoo-module **/
import { Component, useEffect, proxy, onWillStart, types as t, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { FountainDropdown } from "./fountain_widget_component";
import { useService } from "@web/core/utils/hooks";

export class FountainWidget extends Component {
    static template = "FountainWidgetField";
    static components = {
        FountainDropdown,
    };
    props = useProps({
        ...standardFieldProps,
        inputData: t.object().optional(),
    });
    setup() {
        this.orm = useService('orm');
        this.state = proxy({
            childMenu: {},
            activeKeys: [],
            inputData: this.props.record.data[this.props.name],
        });
        useEffect(() => {
            this.state.inputData = this.props.record.data[this.props.name];
        }, () => [this.props.record.data[this.props.name]]);
        onWillStart(async () => {
            this.state.category = await this.orm.searchRead(this.props.record.fields[this.props.name].relation, []);
        });
        this.index = 0; // Track the current depth of the dropdown

        // Bind the onClickDropDown method to ensure `this` refers to the component instance
        this.onClickDropDown = this.onClickDropDown.bind(this);
    }

    get inputData() {
        let val = this.state.inputData;
        let displayName = "";
        if (val) {
            if (Array.isArray(val)) {
                displayName = val[1];
            } else if (typeof val === 'object' && val.display_name) {
                displayName = val.display_name;
            } else if (typeof val === 'string') {
                displayName = val;
            }
        }
        return {
            input: displayName || ''
        };
    }

    get parentMenu() {
        return this.state.category ? this.state.category.filter(item => !item.parent_id) : [];
    }

    get childKeys() {
        return this.state.activeKeys;
    }

    hasChildren(categoryId) {
        return Boolean(
            this.state.category &&
            this.state.category.some(c => c.parent_id && c.parent_id[0] === categoryId)
        );
    }

    onClickDropDown(parent_id, index = 0) {
        // Ensure index is a number, default to 0 if undefined
        index = Number(index) || 0;

        if (this.index >= index) {
            while (this.state.activeKeys.length > index) {
                const keyIndex = this.state.activeKeys.pop();
                delete this.state.childMenu[keyIndex];
            }
            this.index = index;
        }
        let selectedCategory = this.state.category.find((item) => item.id === parent_id);
        let obj = this.state.category.filter(item => item.parent_id && item.parent_id[0] === parent_id);

        if (!this.state.childMenu.hasOwnProperty(parent_id) && obj.length > 0) {
            this.state.childMenu[parent_id] = obj;
            this.state.activeKeys.push(parent_id);
            this.index = index + 1; // Increment index for nested levels
        }

        if (this.props.record && this.props.record.update) {
            this.state.inputData = [parent_id, selectedCategory.complete_name];
            this.props.record.update({ [this.props.name]: { id: parent_id, display_name: selectedCategory.complete_name } });
        } else {
            console.error('Update function not found in record props:', this.props);
        }
        return obj;
    }
}

// Define the widget field with the correct structure
export const FountainWidgetField = {
    component: FountainWidget,
    supportedTypes: ["many2one"],
    extractProps: ({ attrs }) => {
        return {};
    },
};

// Register the widget in the field registry
registry.category("fields").add("fountain_widget", FountainWidgetField);
