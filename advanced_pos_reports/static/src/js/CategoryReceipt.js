/** @odoo-module **/
import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

    export class CategorySummaryReceipt extends Component {
    // Extending Component and Adding Class CategorySummaryReceipt
        static template = 'CategorySummaryReceipt';
        static props = {
            data:{ type: Object },
        }

        setup() {
            super.setup();
        }
    }
