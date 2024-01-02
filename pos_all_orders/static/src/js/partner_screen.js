odoo.define('pos_all_orders.partner_orders', function (require) {
    'use strict';
    const ClientLine = require('point_of_sale.ClientLine');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    var rpc = require('web.rpc')

    const PosOrderPartnerLine = (ClientLine) =>
    class extends ClientLine {
        constructor() {
        super(...arguments);
            super.setup();
            useListener('click-order', this._onClickOrder);
        }
        /**
        * The button for viewing the orders of selected customer
        */
        async _onClickOrder(id) {
            var self = this;
            var query = await rpc.query({
            model: 'pos.session',
            method: 'pos_order_partner',
            args: [id],
        }).then(function(result) {
            self.showScreen('CustomALLOrdrScreen', {
                orders: result,
            });
        });
            this.trigger('close-temp-screen');
        }
    };
Registries.Component.extend(ClientLine, PosOrderPartnerLine);
return ClientLine;
});