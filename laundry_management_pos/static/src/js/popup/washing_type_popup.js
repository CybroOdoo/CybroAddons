/** @odoo-module **/

import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";


export class LaundryServiceTypePopup extends Component {
    static template = "LaundryServiceTypePopup";
    static components = { Dialog };

    setup() {
        this.pos = usePos();
        this.dialog = useService("dialog");
    }
    /**
     * Called when a washing type button is clicked.
     */
    async laundryPopup(event) {
        event.preventDefault();
        event.stopPropagation();
        const order = this.pos.getOrder();
        const line = order?.getSelectedOrderline();

        if (!line) {
            this.props.close();
            return;
        }
        const washingTypeId = parseInt(event.currentTarget.dataset.id);
        this.pos.data.models['pos.order.line'].update(order.getSelectedOrderline(), { washing_type_id:washingTypeId })
        const service = order.getSelectedOrderline().washing_type_id.amount;
        order.getSelectedOrderline().price_unit = service;
        this.props.close();
    }// closes the dialog cleanly
}
