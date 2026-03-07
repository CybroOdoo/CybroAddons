/** @odoo-module */
import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";


    export class PaymentSummaryReceipt extends Component {
    // Extending Component and Adding Class PaymentSummaryReceipt
         static template = 'PaymentSummaryReceipt';
         static props = {
            data:{ type: Object },
        }
         setup() {
            super.setup();
         }

    }
