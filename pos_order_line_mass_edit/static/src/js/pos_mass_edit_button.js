odoo.define('pos_order_line_mass_edit.pos_mass_edit_button', function(require) {
'use strict';
    const Registries = require('point_of_sale.Registries');
    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require("@web/core/utils/hooks");
    class MassEditButton extends PosComponent {
//    Extend the POS session to add order line edit button
      setup() {
          super.setup();
          useListener('click', this.onClick);
      }
     async onClick() {
//     Order line button Onclick()
        var order = this.env.pos.get_order();
        var order_line = order.get_orderlines();
        if (!order_line.length){
//        Popup if no product in pos order line
            return this.showPopup('ErrorPopup', {
                title: this.env._t('Order is Empty'),
                body: this.env._t('You need to add product.'),
            });
        }

        const {confirmed} = await this.showPopup("MassEditPopup", {
//        edit order line button popup action
              title: this.env._t('Edit Order Line'),
              body: order_line,
          });
        }
  }
MassEditButton.template = 'MassEditButton';
  ProductScreen.addControlButton({
      component: MassEditButton,
      condition: function() {
          return this.env.pos;
      },
  });
  Registries.Component.add(MassEditButton);
  return MassEditButton;
});
