/** @odoo-module **/
const ProductScreen = require('point_of_sale.ProductScreen');
const Registries = require('point_of_sale.Registries');
const { Gui } = require('point_of_sale.Gui');

export const PosZeroQuantityRestrictProductScreen = (ProductScreen) =>
  class extends ProductScreen {
    //@override
    async _onClickPay() {
      const orderLines = this.env.pos.get_order().orderlines;
      for (let i = 0; i < orderLines.length; i++) {
        const qty = orderLines[i].quantity;
        if (qty === 0) {
          // Do not confirm the order and show error popup
          Gui.showPopup('ErrorPopup', {
            title: 'Zero quantity not allowed',
            body: 'Only a positive quantity is allowed for confirming the order',
          });
          return; // Exit the loop and do not proceed with confirming the order
        }
      }
      // If all order lines have a positive quantity, call the original _onClickPay method
      await super._onClickPay(...arguments);
    }
  };

Registries.Component.extend(ProductScreen, PosZeroQuantityRestrictProductScreen);
