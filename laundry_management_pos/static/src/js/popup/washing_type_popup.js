/** @odoo-module **/

import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";
import { usePos } from "@point_of_sale/app/store/pos_hook";
/**
 * Popup component for selecting a laundry service type in POS.
 */
export class LaundryServiceTypePopup extends Component {
    static template = "LaundryServiceTypePopup";
    static components = { Dialog };

    /**
     * Component setup: initialize POS and Dialog services.
     */
    setup() {
        this.pos = usePos();
        this.dialog = useService("dialog");
    }
    /**
     * Called when a washing type button is clicked.
     */
        async laundryPopup(event) {
            const order = this.props.pos.get_order();
            const line = order?.get_selected_orderline();

            if (!line) {
                this.props.close();
                return;
            }
            const washing_type_id = parseInt(event.currentTarget.dataset.id);
            this.pos.data.models['pos.order.line'].update(order.get_selected_orderline(), { washing_type_id: washing_type_id })
            const service = order.get_selected_orderline().washing_type_id.amount;
            order.get_selected_orderline().price_unit = service;
            this.props.close();
        }
}
