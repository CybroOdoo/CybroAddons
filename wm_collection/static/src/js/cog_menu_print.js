/** @odoo-module **/

import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, xml } from "@odoo/owl";

const cogMenuRegistry = registry.category("cogMenu");

export class PrintCollectionOrder extends Component {
    static template = xml`<DropdownItem onSelected="() => this.onPrint()">Print Summary Report</DropdownItem>`;
    static components = { DropdownItem };
    static props = {};

    setup() {
        this.action = useService("action");
    }

    onPrint() {
        this.action.doAction("wm_collection.action_wm_collection_order_report_wizard");
    }
}

export const printCollectionOrderItem = {
    Component: PrintCollectionOrder,
    groupNumber: 10,
    isDisplayed: (env) =>
        env.config.viewType === "list" &&
        env.searchModel.resModel === "wm.collection.order",
};

cogMenuRegistry.add("print-collection-order-menu", printCollectionOrderItem, { sequence: 16 });

