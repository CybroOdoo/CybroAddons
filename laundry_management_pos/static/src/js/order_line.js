/** @odoo-module **/

import { Orderline } from "@point_of_sale/app/generic_components/orderline/orderline";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { LaundryServiceTypePopup } from "@laundry_management_pos/js/popup/washing_type_popup";

patch(Orderline.prototype, {
    /**
     * Setup the orderline with mandatory laundry fields.
     */
    setup() {
        super.setup(...arguments);
        this.pos = usePos();
        this.dialog = useService("dialog");
    },

    /**
     * Button click: open dialog to select washing type.
     */
    async click() {
        const orderline = this.props.line;
        if (!this.pos?.washing_type?.length) {
            // washing type not loaded
            return this.dialog.add(AlertDialog, {
                title: _t("No Laundry Services"),
                body: _t("Please configure washing types in the backend."),
            });
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
     * Function to set the selected washing type.
     * @param {Object} service - The washing service details.
     */
    set_washing_type(service) {
        this.washing_type = service.name;
        this.washing_type_id_custom = service.id;
        this.washing_type_price = service.amount;
        this.price = service.amount;

        this.raw.washing_type = service.name;
        this.raw.washing_type_id_custom = service.id;

        this.raw.washing_type_id = service.id;
        this.raw.washing_type_price = service.amount;
    },

    /**
     * Remove washing type.
     */
    remove_laundry() {
    const order = this.pos.get_order();
    const line = order.get_selected_orderline();

    // ✅ Ensure an orderline is selected
    if (!line) {
        this.dialog.add(AlertDialog, {
            title: _t("No Orderline Selected"),
            body: _t("Please select an orderline to remove the laundry service."),
        });
        return;
    }

    // Restore original product price
    line.price_unit = line.product_id.lst_price;

    // Remove washing type
    this.pos.data.models["pos.order.line"].update(line, {
        washing_type_id: false,
    });
},

});
