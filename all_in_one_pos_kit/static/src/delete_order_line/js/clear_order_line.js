odoo.define('all_in_one_pos_kit.DeleteOrderLines', function(require) {
    //Represents a custom component for deleting order lines in the Point of Sale.
    'use strict';
    // Import required dependencies
    const Registries = require('point_of_sale.Registries');
    const Orderline = require('point_of_sale.Orderline');
    const OrderWidget = require('point_of_sale.OrderWidget');
    const OrderLineDelete = (Orderline) =>class extends Orderline {// Extend the Orderline component with custom functionality
        async clear_button_fun() {//Function to clear order line product
           this.trigger('numpad-click-input', { key: 'Backspace' });
           this.trigger('numpad-click-input', { key: 'Backspace' });
        }
    };
    Registries.Component.extend(Orderline, OrderLineDelete);
    return OrderWidget;
});
