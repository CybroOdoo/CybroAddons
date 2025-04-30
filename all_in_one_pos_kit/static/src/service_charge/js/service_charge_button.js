odoo.define('all_in_one_pos_kit.ServiceChargeButton', function (require) {
    'use strict';

    const models = require('point_of_sale.models');
    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require("@web/core/utils/hooks");
    // Load custom configuration settings fields
    models.load_models([{
        model: 'pos.config',
        fields: ['enable_service_charge', 'visibility', 'global_selection', 'global_charge', 'global_product_id', 'is_customer_details', 'is_customer_name', 'is_customer_address', 'is_customer_mobile', 'is_customer_phone', 'is_customer_email', 'is_customer_vat', 'is_qr_code', 'is_invoice_number'],
        loaded: function (self, pos_config) {
            self.pos_config = Object.assign({}, self.pos_config, pos_config[0]);
        }
    }]);

    class ServiceChargeButton extends PosComponent {
        setup() {
            super.setup();
            useListener('click', this._onClick);
        }

        async _onClick(event) {
            var self = this;
            let res_config_settings = await this.rpc({
                model: 'pos.config',
                method: 'search_read',
                args: [[], ['enable_service_charge', 'visibility', 'global_selection', 'global_charge', 'global_product_id']],
                limit: 1,
            });
            if (res_config_settings.length === 0) {
                await this.showPopup('ErrorPopup', {
                    title: this.env._t("Configuration Error"),
                    body: this.env._t("No configuration settings found."),
                });
                return;
            }
            res_config_settings = res_config_settings[0];
            if (!res_config_settings.enable_service_charge) {
                await this.showPopup('ErrorPopup', {
                    title: this.env._t("Service Charge Disabled"),
                    body: this.env._t("Service charge is not enabled in the settings."),
                });
                return;
            }
            var order = this.env.pos.get_order();
            var lines = order.get_orderlines();

            if (res_config_settings.visibility === 'global') {
                var product = this.env.pos.db.get_product_by_id(res_config_settings.global_product_id[0]);
                if (!product) {
                    await this.showPopup('ErrorPopup', {
                        title: this.env._t("No service product found"),
                        body: this.env._t("The service product seems misconfigured. Make sure it is flagged as 'Can be Sold' and 'Available in Point of Sale'."),
                    });
                    return;
                }
                lines.filter(line => line.get_product() === product)
                    .forEach(line => order.remove_orderline(line));
                const { confirmed, payload } = await this.showPopup('NumberPopup', {
                    title: this.env._t('Service Charge'),
                    startingValue: res_config_settings.global_charge,
                    isInputSelected: true
                });
                if (confirmed && payload > 0) {
                    if (res_config_settings.global_selection === 'amount') {
                        order.add_product(product, { price: payload });
                    } else {
                        order.add_product(product, { price: payload / 100 * order.get_total_with_tax() });
                    }
                }
            } else {
                var product = this.env.pos.db.get_product_by_id(this.env.pos.config.service_product_id[0]);
                if (!product) {
                    await this.showPopup('ErrorPopup', {
                        title: this.env._t("No service product found"),
                        body: this.env._t("The service product seems misconfigured. Make sure it is flagged as 'Can be Sold' and 'Available in Point of Sale'."),
                    });
                    return;
                }
                lines.filter(line => line.get_product() === product)
                    .forEach(line => order.remove_orderline(line));
                const { confirmed, payload } = await this.showPopup('NumberPopup', {
                    title: this.env._t('Service Charge'),
                    startingValue: this.env.pos.config.service_charge,
                    isInputSelected: true
                });
                if (confirmed && payload > 0) {
                    if (this.env.pos.config.charge_type === 'amount') {
                        order.add_product(product, { price: payload });
                    } else {
                        order.add_product(product, { price: payload / 100 * order.get_total_with_tax() });
                    }
                }
            }
        }
    }
    ServiceChargeButton.template = 'ServiceChargeButton';

    ProductScreen.addControlButton({
        component: ServiceChargeButton,
        condition: function() {
            return true;
        },
    });
    Registries.Component.add(ServiceChargeButton);
    return ServiceChargeButton;
});