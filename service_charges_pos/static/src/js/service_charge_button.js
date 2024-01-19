/** @odoo-module */
import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { _t } from "@web/core/l10n/translation";

export class ServiceChargeButton extends Component {
    static template = "service_charges_pos.ServiceChargeButton";
    setup() {
        this.pos = usePos();
        this.popup = useService("popup");
    }
    async click() {
        // To show number pop up and service charge applying functions based on conditions.
        let res_config_settings = this.pos.res_config_settings[this.pos.res_config_settings.length -1]
        var global_selection = res_config_settings.global_selection
        var global_charge = res_config_settings.global_charge
        var visibility = res_config_settings.visibility
        var global_product = res_config_settings.global_product_id[0]
        var order = this.pos.get_order();
        var lines = order.get_orderlines();
        if (visibility == 'global') {
            var product = this.pos.db.get_product_by_id(global_product)
            if (product === undefined) {
                await this.popup.add(ErrorPopup, {
                    title: _t("No service product found"),
                    body: _t("The service product seems misconfigured. Make sure it is flagged as 'Can be Sold' and 'Available in Point of Sale'.")
                });
                return
            }
            // Remove existing discounts
            lines.filter(line => line.get_product() === product).forEach(line => order.removeOrderline(line));
            const { confirmed, payload } = await this.popup.add(NumberPopup, {
                title: _t('Service Charge'),
                startingValue: parseInt(global_charge),
                isInputSelected: true
            })
            if (confirmed) {
                if (payload > 0) {
                    if (global_selection == 'amount') {
                        order.add_product(product, {
                            price: payload
                        });
                    } else {
                        var total_amount = order.get_total_with_tax()
                        var per_amount = payload / 100 * total_amount
                        order.add_product(product, {
                            price: per_amount
                        });
                    }
                }
            }
        } else {
            var type = this.pos.config.charge_type
            var product = this.pos.db.get_product_by_id(this.pos.config.service_product_id[0]);
            if (product === undefined) {
                await this.popup.add(ErrorPopup, {
                    title: _t("No service product found"),
                    body: _t("The service product seems misconfigured. Make sure it is flagged as 'Can be Sold' and 'Available in Point of Sale'."),
                });
                return;
            }
            lines.filter(line => line.get_product() === product).forEach(line => order.removeOrderline(line));
            const {confirmed, payload } = await this.popup.add(NumberPopup, {
                title: _t('Service Charge'),
                startingValue: this.pos.config.service_charge,
                isInputSelected: true
            })
            if (confirmed) {
                if (payload > 0) {
                    if (type == 'amount') {
                        order.add_product(product, {
                            price: payload
                        });
                    } else {
                        var total_amount = order.get_total_with_tax()
                        var per_amount = payload / 100 * total_amount
                        order.add_product(product, {
                            price: per_amount
                        });
                    }
                }
            }
        }
    }
}
ProductScreen.addControlButton({
    component: ServiceChargeButton,
    condition: function () {
        let res_config_settings = this.pos.res_config_settings[this.pos.res_config_settings.length -1]
        if (res_config_settings) {
            return res_config_settings.enable_service_charge
        } else {
            return false
        }
    },
});
