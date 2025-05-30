/** @odoo-module */
import publicWidget from '@web/legacy/js/public/public_widget';
import { jsonrpc } from "@web/core/network/rpc_service";
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
                jsonrpc('/shop/cart/set_delivery_date',{
                    'delivery_date': delivery_date,
                    'line_id': line_id
                });
            }
            else if (ev.currentTarget.id == 'slot_id') {
                var delivery_slot = ev.currentTarget.value
                var line_id = $(ev.currentTarget).attr('data-line-id')
                jsonrpc('/shop/cart/set_delivery_slot',{
                    'delivery_slot': delivery_slot,
                    'line_id': line_id
                });
            }
        },
    });
