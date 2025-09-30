/** @odoo-module */

import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { reactive } from "@odoo/owl";

patch(ControlButtons.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
    },

    async onClick() {
        await this.dialog.add(NumberPopup, {
            title: _t("Service Charge"),
            startingValue: this.pos.config.service_charge,
            getPayload: (num) => {
                const val = Math.max(
                    0,
                    Math.min(100, this.env.utils.parseValidFloat(num.toString()))
                );
                if (val > 0) {
                    this.apply_service_charge(val);
                }
            },
        });
    },

    async apply_service_charge(val) {
        const order = this.pos.get_order();
        const lines = order.get_orderlines();
        const product = this.pos.config.service_product_id;

        if (!product) {
            this.dialog.add(AlertDialog, {
                title: _t("Missing Product"),
                body: _t("Service product is not configured in POS settings."),
            });
            return;
        }
        lines
            .filter((line) => line.get_product() === product)
            .forEach((line) => order.removeOrderline(line));

        // Calculate service charge amount
        const sc_price =
            this.pos.config.service_charge_type === "amount"
                ? val
                : (order.get_total_with_tax() * val) / 100;

        // Add service charge line
        await reactive(this.env.services.pos).addLineToCurrentOrder({
            product_id: product.id,
            price_unit: sc_price,
            tax_ids: [],
        });
    },
});
