/** @odoo-module */

import { Orderline } from "@point_of_sale/app/components/orderline/orderline";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { LaundryServiceTypePopup } from "@laundry_management_pos/js/popup/washing_type_popup";

patch(Orderline.prototype, {
    /**
     * Set up pos and dialog service references for this component.
     */
    setup() {
        super.setup(...arguments);
        this.pos = usePos();
        this.dialog = useService("dialog");
    },

    /**
     * Handle click on the orderline laundry icon.
     * Opens the washing type selection popup or shows an error if none configured.
     */
    async click(orderline) {
         if (!orderline.isSelected()) {
            const order = this.pos.getOrder()
            order.selectOrderline(orderline);
        }
        if (!this.pos?.washing_type?.length) {
            this.dialog.add(AlertDialog, {
                title: _t("No Laundry Services"),
                body: _t("Please configure washing types in the backend."),
            });
            return;
        }
        this.dialog.add(LaundryServiceTypePopup, {
            title: _t("Laundry Service"),
            body: _t("Choose the Washing type"),
            service: this.pos.washing_type,
            pos: this.pos,
            orderline: this.props.line,
        });
    },

    /**
     * Remove the assigned washing type from the selected orderline
     * and reset the price to the product's default sales price.
     */
    remove_laundry(orderline) {
    if (!orderline.isSelected()) {
            const order = this.pos.getOrder()
            order.selectOrderline(orderline);
        }
        const order = this.pos.getOrder();
        const line = order?.getSelectedOrderline();
        if (line) {
            this.pos.data.models["pos.order.line"].update(line, {
                price_unit: line.product_id.lst_price,
                washing_type_id: false,
            });
        }
    },
});
