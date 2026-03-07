/** @odoo-module **/
import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

    export class LocationSummaryReceipt extends Component{
    // Extending Component and Adding Class LocationSummaryReceipt
        static template = 'LocationSummaryReceipt';
        static props = {
            data:{ type: Object },
        }

        setup() {
            super.setup();
        }
    }
