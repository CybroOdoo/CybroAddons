/** @odoo-module **/
const ProductScreen = require('point_of_sale.ProductScreen');
const Registries = require('point_of_sale.Registries');
const { Gui } = require('point_of_sale.Gui');

export const PosZeroQuantityRestrictProductScreen = (ProductScreen) =>
    class extends ProductScreen {
        //@override
        async _onClickPay() {
            for (var i = 0; i < this.env.pos.get_order().orderlines.length; i++) {
                //   get orderline quantity
                var qty = this.env.pos.get_order().orderlines[this.env.pos.get_order().orderlines.length - 1].quantity
                if (qty !== 0){
                    await super._onClickPay(...arguments);
                }else {
                     // do not confirm the order and show error popup;
                    Gui.showPopup('ErrorPopup', {
                            title: ('Zero quantity not allowed'),
                            body: ('Only a positive quantity is allowed for confirming the order')
                        });
                    }
            }
        }
    };
Registries.Component.extend(ProductScreen, PosZeroQuantityRestrictProductScreen);