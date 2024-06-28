/** @odoo-module*/
import { registry } from "@web/core/registry";
    /**
    *Action for open the print screen
    */
registry.category("ir.actions.report handlers").add("xlsx", async (action) => {
    var printWindow = window.open(action.data).print();
})
