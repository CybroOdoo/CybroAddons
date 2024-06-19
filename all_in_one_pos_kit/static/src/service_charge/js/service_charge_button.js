odoo.define('all_in_one_pos_kit.ServiceChargeButton', function(require) {
    'use strict';
    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const {
        useListener
    } = require("@web/core/utils/hooks");
    var rpc = require('web.rpc');
    class ServiceChargeButton extends PosComponent {
        setup() {
            super.setup();
            useListener('click', this._onClick);
        }
        async _onClick() { //Click button service charge
            var self = this;
            let res_config_settings = self.env.pos.res_config_settings[self.env.pos.res_config_settings.length - 1]
            var order = this.env.pos.get_order();
            var lines = order.get_orderlines();
            if (res_config_settings.visibility == 'global') {
                var product = this.env.pos.db.get_product_by_id(res_config_settings.global_product_id[0])
                if (product === undefined) {
                    await this.showPopup('ErrorPopup', {
                        title: this.env._t("No service product found"),
                        body: this.env._t("The service product seems misconfigured. Make sure it is flagged as 'Can be Sold' and 'Available in Point of Sale'."),
                    });
                    return;
                }
                // Remove existing discounts
                lines.filter(line => line.get_product() === product)
                    .forEach(line => order.remove_orderline(line));
                const {
                    confirmed,
                    payload
                } = await this.showPopup('NumberPopup', {
                    title: this.env._t('Service Charge'),
                    startingValue: parseInt(res_config_settings.global_charge),
                    isInputSelected: true
                });
                if (confirmed)
                    if (payload > 0) {
                        if (res_config_settings.global_selection == 'amount') {
                            order.add_product(product, {
                                price: payload
                            });
                        } else {
                            order.add_product(product, {
                                price: payload / 100 * order.get_total_with_tax()
                            });
                        }
                    }

            } else {
                var product = this.env.pos.db.get_product_by_id(this.env.pos.config.service_product_id[0]);
                if (product === undefined) {
                    await this.showPopup('ErrorPopup', {
                        title: this.env._t("No service product found"),
                        body: this.env._t("The service product seems misconfigured. Make sure it is flagged as 'Can be Sold' and 'Available in Point of Sale'."),
                    });
                    return;
                }
                // Remove existing discounts
                lines.filter(line => line.get_product() === product)
                    .forEach(line => order.remove_orderline(line));
                const {
                    confirmed,
                    payload
                } = await this.showPopup('NumberPopup', {
                    title: this.env._t('Service Charge'),
                    startingValue: this.env.pos.config.service_charge,
                    isInputSelected: true
                });
                if (confirmed)
                    if (payload > 0) {
                        if (this.env.pos.config.charge_type == 'amount') {
                            order.add_product(product, {
                                price: payload
                            });
                        } else {
                            order.add_product(product, {
                                price: payload / 100 * order.get_total_with_tax()
                            });
                        }
                    }
            }
        }
    }
    ServiceChargeButton.template = 'service_charges_pos.ServiceChargeButton';
    ProductScreen.addControlButton({
        component: ServiceChargeButton,
        condition: function() {
            return true
        },
    });
    Registries.Component.add(ServiceChargeButton);
    return ServiceChargeButton;
});
