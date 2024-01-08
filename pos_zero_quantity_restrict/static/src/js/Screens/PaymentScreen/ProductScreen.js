/** @odoo-module **/
const ProductScreen = require('point_of_sale.ProductScreen');
const Registries = require('point_of_sale.Registries');
const { Gui } = require('point_of_sale.Gui');

/**
Extend ProductScreen to super the function _onClickPay
**/
export const PosZeroQuantityRestrictProductScreen = (ProductScreen) =>
  class extends ProductScreen {
    /** Super _onClickPay to show an error message when product have zero qty in
     order line
    **/
    async _onClickPay() {
      const orderLines = this.env.pos.get_order().orderlines;
      for (let i = 0; i < orderLines.models.length; i++) {
        const qty = orderLines.models[i].quantity;
        if (qty === 0) {
          /** Do not confirm the order and show error popup **/
          Gui.showPopup('ErrorPopup', {
            title: 'Zero quantity not allowed',
            body: 'Only a positive quantity is allowed for confirming the order',
          });
          /**Exit the loop and do not proceed with confirming the order**/
          return;
        }
      }
      /** If all order lines have a positive quantity, call the original _onClickPay method **/
      await super._onClickPay(...arguments);
    }
  };
Registries.Component.extend(ProductScreen, PosZeroQuantityRestrictProductScreen);
