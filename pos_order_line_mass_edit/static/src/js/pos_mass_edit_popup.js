odoo.define('pos_order_line_mass_edit.pos_mass_edit_popup', function(require) {
'use strict';
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    class MassEditPopup extends AbstractAwaitablePopup {
        async confirm(event){
    //    function for confirm button inside popup
            var order = this.env.pos.get_order();
            var order_lines = order.get_orderlines();
            var pop = this.props.body

            for (var i = 0; i < order_lines.length; i++) {
                for (var j = 0; j < pop.length; j++) {
                    if (order_lines[i].id === pop[j].id) {
                        order_lines[i].set_quantity(pop[j].quantity);
                        order_lines[i].set_discount(pop[j].discount);
                        order_lines[i].set_unit_price(pop[j].price);
                        order_lines[i].price_manually_set = true;
                        order_lines[i].price_automatically_set = false;
                        order.trigger('change', order_lines[i]);
                    }
                }
            }
            window.location.reload();
        }

        sendInput(key) {
//            function to remove order line from product screen
            var order = this.env.pos.get_order();
            var order_lines = order.get_orderlines();

            for (var i = 0; i < order_lines.length; i++) {
                if (order_lines[i].id === key) {
                    order.remove_orderline(order_lines[i])
                }
            }
            this.cancel(); ///close popup
            this.showPopup("MassEditPopup", {
    //        edit order line button popup action
                title: this.env._t('Edit Order Line'),
                body: order_lines,
            });

        }

        async clear_button() {
              const { confirmed} = await this.showPopup("ConfirmPopup", {
                     title: this.env._t('Clear Orders?'),
                     body: this.env._t('Are you sure you want to delete all orders from the cart?'),
                 });
              if(confirmed){
                  const order = this.env.pos.get_order();
                  order.remove_orderline(order.get_orderlines());
              }
        }

    }
    MassEditPopup.template = 'MassEditPopup';
    MassEditPopup.defaultProps = {
    confirm: "Confirm",
    cancel: "Cancel",
    };
  Registries.Component.add(MassEditPopup);
  return MassEditPopup;
});
