odoo.define('pos_product_stock.Custom', function(require) {
    'use strict';
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const order = (ProductScreen) => class extends ProductScreen {
        //we extends ProductScreen to super _clickproduct function.
        async _clickProduct(event) {
            if (event.detail.detailed_type == 'product') {
                if (this.env.pos.res_setting['stock_from'] == 'all_warehouse') {
                    if (this.env.pos.res_setting['stock_type'] == 'on_hand') {
                        if (event.detail.qty_available <= event.detail.deny) {
                            const body = _.str.sprintf(this.env._t('%s is Out Of Stock'), event.detail.display_name);
                            await this.showPopup('ErrorPopup', {
                                title: this.env._t('Deny Order'),
                                body
                            }); //shows error pop up as condition satisfies.
                        } else {
                            super._clickProduct(event);
                        }
                    } else if (this.env.pos.res_setting['stock_type'] == 'outgoing_qty') {
                        if (event.detail.outgoing_qty <= event.detail.deny) {
                            const body = _.str.sprintf(this.env._t('%s is Out Of Stock'), event.detail.display_name);
                            await this.showPopup('ErrorPopup', {
                                title: this.env._t('Deny Order'),
                                body
                            });
                        } else {
                            super._clickProduct(event);
                        }
                    } else if (this.env.pos.res_setting['stock_type'] == 'incoming_qty') {
                        if (event.detail.incoming_qty <= event.detail.deny) {
                            const body = _.str.sprintf(this.env._t('%s is Out Of Stock'), event.detail.display_name);
                            await this.showPopup('ErrorPopup', {
                                title: this.env._t('Deny Order'),
                                body
                            });
                        } else {
                            super._clickProduct(event);
                        }
                    } else if (this.env.pos.res_setting['stock_type'] == 'available_qty') {
                        if (event.detail.available_product <= event.detail.deny) {
                            const body = _.str.sprintf(this.env._t('%s is Out Of Stock'), event.detail.display_name);
                            await this.showPopup('ErrorPopup', {
                                title: this.env._t('Deny Order'),
                                body
                            });
                        } else {
                            super._clickProduct(event);
                        }
                    }
                } else if (this.env.pos.res_setting['stock_from'] == 'current_warehouse') {
                    if (this.env.pos.res_setting['stock_type'] == 'on_hand') {
                        if (event.detail.on_hand <= event.detail.deny) {
                            const body = _.str.sprintf(this.env._t('%s is Out Of Stock'), event.detail.display_name);
                            await this.showPopup('ErrorPopup', {
                                title: this.env._t('Deny Order'),
                                body
                            });
                        } else {
                            super._clickProduct(event);
                        }
                    } else if (this.env.pos.res_setting['stock_type'] == 'outgoing_qty') {
                        if (event.detail.outgoing <= event.detail.deny) {
                            const body = _.str.sprintf(this.env._t('%s is Out Of Stock'), event.detail.display_name);
                            await this.showPopup('ErrorPopup', {
                                title: this.env._t('Deny Order'),
                                body
                            });
                        } else {
                            super._clickProduct(event);
                        }
                    } else if (this.env.pos.res_setting['stock_type'] == 'incoming_qty') {
                        if (event.detail.incoming <= event.detail.deny) {
                            const body = _.str.sprintf(this.env._t('%s is Out Of Stock'), event.detail.display_name);
                            await this.showPopup('ErrorPopup', {
                                title: this.env._t('Deny Order'),
                                body
                            });
                        } else {
                            super._clickProduct(event);
                        }
                    } else if (this.env.pos.res_setting['stock_type'] == 'available_qty') {
                        if (event.detail.available <= event.detail.deny) {
                            const body = _.str.sprintf(this.env._t('%s is Out Of Stock'), event.detail.display_name);
                            await this.showPopup('ErrorPopup', {
                                title: this.env._t('Deny Order'),
                                body
                            });
                        } else {
                            super._clickProduct(event);
                        }
                    }
                }
            } else {
                super._clickProduct(event);
            }
        }
    }
    Registries.Component.extend(ProductScreen, order);
});
