odoo.define('membership_in_pos.customer', function (require) {
"use strict";
    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen');
    var { Gui } = require('point_of_sale.Gui');
    var core = require('web.core');
    var _t = core._t;
    const PosCustomer = (ProductScreen) =>
        class extends ProductScreen {
            setup(){
                super.setup();
            }
            //To check where the customer has to be selected
             async _onClickPay() {
                 if (this.env.pos.get_order().get_partner()){
                    if (this.env.pos.get_order().orderlines.some(line => line.get_product().tracking !== 'none' && !line.has_valid_product_lot()) && (this.env.pos.picking_type.use_create_lots || this.env.pos.picking_type.use_existing_lots)) {
                        const { confirmed } = await this.showPopup('ConfirmPopup', {
                        title: this.env._t('Some Serial/Lot Numbers are missing'),
                        body: this.env._t('You are trying to sell products with serial/lot numbers, but some of them are not set.\nWould you like to proceed anyway?'),
                        confirmText: this.env._t('Yes'),
                        cancelText: this.env._t('No')
                        });
                        if (confirmed) {
                            this.showScreen('PaymentScreen');
                        }
                    } else {
                        this.showScreen('PaymentScreen');
                    }
                 }
                else{
                    Gui.showPopup("ErrorPopup", {
                    'title': _t("Customer"),
                    'body':  _t("You Must Select a Customer"),
                    });
                }
             }
        }
    Registries.Component.extend(ProductScreen, PosCustomer);
    return ProductScreen;
});
