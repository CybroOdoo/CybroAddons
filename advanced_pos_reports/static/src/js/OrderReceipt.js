/** @odoo-module */
import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

    export class OrderSummaryReceipt extends Component {
    // Extending Component and Adding Class OrderSummaryReceipt
         static template = 'OrderSummaryReceipt';
         static props = {
            data:{ type: Object },
        }
         setup() {
            super.setup();
        }
    }
