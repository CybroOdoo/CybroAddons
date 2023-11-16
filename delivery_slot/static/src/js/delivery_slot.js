odoo.define('delivery_slot.cart_line', function(require) {
    'use strict';
    /**
     * Module for handling delivery slot selection in the shopping cart.
     */
    var publicWidget = require('web.public.widget');
    const ajax = require('web.ajax');
    publicWidget.registry.websiteDeliverySlot = publicWidget.Widget.extend({
        selector: '.delivery_slot_div',
        events: {
            'change #slot_id': '_onDateChange',
            'change #date': '_onDateChange',
        },
        /**
         * Handles the change event of the date or slot selection.
         * @param {Event} ev - The change event.
         */
        _onDateChange: function(ev) {
            if (ev.currentTarget.id == 'date') {
                var delivery_date = ev.currentTarget.value
                var line_id = $(ev.currentTarget).attr('data-line-id')
                ajax.jsonRpc('/shop/cart/set_delivery_date', "call", {
                    'delivery_date': delivery_date,
                    'line_id': line_id
                });
            }
            else if (ev.currentTarget.id == 'slot_id') {
                var delivery_slot = ev.currentTarget.value
                var line_id = $(ev.currentTarget).attr('data-line-id')
                ajax.jsonRpc('/shop/cart/set_delivery_slot', "call", {
                    'delivery_slot': delivery_slot,
                    'line_id': line_id
                });
            }
        },
    });
});
