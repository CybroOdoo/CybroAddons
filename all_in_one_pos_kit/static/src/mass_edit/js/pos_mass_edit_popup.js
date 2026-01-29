odoo.define('all_in_one_pos_kit.pos_mass_edit_popup', function(require) {
    'use strict';
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');

    class MassEditPopup extends AbstractAwaitablePopup {
        async confirm() {
            // Get the current order
            const order = this.env.pos.get_order();
            // Iterate through each order line and update the quantity and other fields
            this.props.body.forEach(line => {
                let orderLine = order.get_orderline(line.id);
                if (orderLine) {
                    orderLine.set_quantity(line.quantity);
                    orderLine.set_unit_price(line.price);
                    if (this.env.pos.config.manual_discount) {
                        orderLine.set_discount(line.discount);
                    }
                }
            });
            // Close the popup
            this.trigger('close-popup');
        }
        sendInput(key) {
            this.props.body.forEach(edit => {
                if (edit.id == key) {
                    edit.quantity = 0;
                }
            });
            this.render();
        }
    }
    MassEditPopup.template = 'MassEditPopup';
    MassEditPopup.defaultProps = {
        confirmText: "Confirm",
        cancelText: "Cancel",
    };
    Registries.Component.add(MassEditPopup);
    return MassEditPopup;
});
