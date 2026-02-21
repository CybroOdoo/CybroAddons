/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { Orderline } from "@point_of_sale/app/store/models";

// Patch to add + and - button functionality in POS order line.
patch(Orderline.prototype, {

    //Increase the quantity of the order line by 1.
    onclick_plus() {
        this.props.line.line.set_quantity(parseInt(this.props.line.qty) + 1);
    },

    //Decrease the quantity of the order line by 1, only if qty is not 0.
    onclick_minus() {
        if (this.props.line.qty != 0) {
            this.props.line.line.set_quantity(parseInt(this.props.line.qty) - 1);
        }
    },

    //Return display data including the custom plus/minus functions.
    getDisplayData() {
        return {
            ...super.getDisplayData(),
            onclick_plus: this.onclick_plus,
            onclick_minus: this.onclick_minus,
            line: this,
        };
    }
});
