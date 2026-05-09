/** @odoo-module */
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";
import { _t } from "@web/core/l10n/translation";

patch(ControlButtons.prototype, {
    async clickServiceCharge() {
        const config = this.pos.config;
        if (!config.enable_service_charge) {
            return;
        }
        // Close the Actions popup if open
        if (this.props.close) {
            this.props.close();
        }
        var order = this.pos.get_order();
        var lines = order.lines;
        var visibility = config.sc_visibility;

        if (visibility === 'global') {
            var global_product_id = config.global_product_id;
            var global_charge = config.global_charge;
            var global_selection = config.global_selection;
            var product = this.pos.models['product.product'].get(global_product_id);
            if (!product) {
                this.dialog.add(AlertDialog, {
                    title: _t("No service product found"),
                    body: _t("The service product seems misconfigured. Make sure it is flagged as 'Can be Sold' and 'Available in Point of Sale'.")
                });
                return;
            }
            // Remove existing service lines
            var existingLines = lines.filter(line => line.product_id.id === product.id);
            for (const line of existingLines) {
                order.removeOrderline(line);
            }

            const payload = await makeAwaitable(this.dialog, NumberPopup, {
                title: _t('Service Charge'),
                startingValue: global_charge
            });

            if (payload !== false && payload !== undefined) {
                const amount = parseFloat(payload);
                if (amount > 0) {
                    if (global_selection === 'amount') {
                        await this.pos.addLineToCurrentOrder(
                            { product_id: product, price_unit: amount },
                            {},
                            false
                        );
                    } else {
                        var total_amount = order.get_total_with_tax();
                        var per_amount = amount / 100 * total_amount;
                        await this.pos.addLineToCurrentOrder(
                            { product_id: product, price_unit: per_amount },
                            {},
                            false
                        );
                    }
                }
            }
        } else {
            // Session mode
            if (!config.is_service_charges) {
                return;
            }
            var type = config.charge_type;
            var product = config.service_product_id;
            if (!product) {
                this.dialog.add(AlertDialog, {
                    title: _t("No service product found"),
                    body: _t("The service product seems misconfigured. Make sure it is flagged as 'Can be Sold' and 'Available in Point of Sale'."),
                });
                return;
            }
            var existingLines = lines.filter(line => line.product_id.id === product.id);
            for (const line of existingLines) {
                order.removeOrderline(line);
            }

            const payload = await makeAwaitable(this.dialog, NumberPopup, {
                title: _t('Service Charge'),
                startingValue: config.service_charge
            });

            if (payload !== false && payload !== undefined) {
                const amount = parseFloat(payload);
                if (amount > 0) {
                    if (type === 'amount') {
                        await this.pos.addLineToCurrentOrder(
                            { product_id: product, price_unit: amount },
                            {},
                            false
                        );
                    } else {
                        var total_amount = order.get_total_with_tax();
                        var per_amount = amount / 100 * total_amount;
                        await this.pos.addLineToCurrentOrder(
                            { product_id: product, price_unit: per_amount },
                            {},
                            false
                        );
                    }
                }
            }
        }
    }
});
