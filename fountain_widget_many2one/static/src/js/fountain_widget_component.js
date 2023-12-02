/** @odoo-module **/
import { Dropdown } from "@web/core/dropdown/dropdown";
//Extending the Dropdown and adding the inputData into the props
export class FountainDropdown extends Dropdown { }
FountainDropdown.template = "fountain.Dropdown"
FountainDropdown.props = {
    ...Dropdown.props,
    inputData: { type: Object, optional: true }
}
