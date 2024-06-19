odoo.define('pos_book_order.TicketScreen', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const TicketScreen = require('point_of_sale.TicketScreen');
    const Registries = require('point_of_sale.Registries');
    const { useAutofocus } = require("@web/core/utils/hooks");
    const { parse } = require('web.field_utils');
    const { useState } = owl;

    const BookOrderTicketScreen = (TicketScreen) =>
        class extends TicketScreen {
         async  _onClickOrder({ detail: clickedOrder }) {
                    if (clickedOrder.booking_ref_id && !clickedOrder.is_paid()){
                    const {confirmed} = await this.showPopup('ConfirmPopup', {
                            title: this.env._t('Confirm Booking'),
                            body: this.env._t('You have to confirm the booking to choose this order'),
                        });
                    if (confirmed) {
                    var self = this
                    await this.rpc({
                        model: 'book.order',
                        method: 'all_orders',
                    }).then(function(result) {
                        self.showScreen('BookedOrdersScreen', {
                            data: result,
                            new_order: false,
                        });
                    })
                    }
                    }
                    else{
                    return super._onClickOrder({ detail: clickedOrder });
                    }
                }
        };

    Registries.Component.extend(TicketScreen, BookOrderTicketScreen);
});
