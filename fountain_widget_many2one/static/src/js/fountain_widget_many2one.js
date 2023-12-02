/** @odoo-module **/
import { Component, useState, useEffect, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { FountainDropdown } from "./fountain_widget_component"
import { useService } from '@web/core/utils/hooks';

export class FountainWidget extends Component {
    //Extending component and creating a new widget
    setup() {
        this.orm = useService('orm');
        useEffect(() => { this.state.inputData = this.props.record.data[this.props.name] }, () => [this.props])
        this.state = useState({
            childMenu: {},
            inputData: this.props.record.data[this.props.name]
        });
        onWillStart(async () => {
            this.state.category = await this.orm.searchRead(this.props.record.fields[this.props.id].relation, []);
        });
        this.index = 0
    }
    //    Function for returning the data to be inserted in the input
    get inputData() {
        return {
            input: this.state.inputData[1]
        }
    }
    //    Function to get parent records
    get parentMenu() {
        return this.state.category.filter(item => !item.parent_id)
    }
    //    Function to get child records
    get childKeys() {
        return Object.keys(this.state.childMenu)
    }
    //    Click function of the options
    onClickDropDown(parent_id, index = 0) {
        if (this.index >= index) {
            let childLength = this.childKeys.length
            while (index < childLength) {
                const keyIndex = this.childKeys[index]
                delete this.state.childMenu[keyIndex]
                childLength--
            }
        }
        let obj = this.state.category.filter(item => item.parent_id[0] === parent_id)
        if (!this.state.childMenu.hasOwnProperty(parent_id) && obj.length > 0) {
            this.state.childMenu[parent_id] = obj
            this.index = index;
        }
        this.props.update([parent_id])
        return obj
    }
}
FountainWidget.template = 'FountainWidgetField';
FountainWidget.components = {
    Dropdown,
    DropdownItem,
    FountainDropdown,
};
FountainWidget.props = {
    ...standardFieldProps,
};
FountainWidget.supportedTypes = ["many2one"];
registry.category("fields").add("fountain_widget", FountainWidget);
