/** @odoo-module */
import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

    export class ProductSummaryReceipt extends Component {
    // Extending Component and Adding Class CategorySummaryReceipt
         static template = 'ProductSummaryReceipt';
         static props = {
            data:{ type: Object },
        }
         setup() {
            super.setup();
         }

    }
