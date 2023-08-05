odoo.define('pos_all_orders.ClientLine', function (require) {
    'use strict';
    const ClientListScreen = require('point_of_sale.ClientLine');
    const Registries = require('point_of_sale.Registries');
    const { useListener } =require("@web/core/utils/hooks");
    var rpc = require('web.rpc');

    const PosOrderPartnerLine = (ClientLine) =>
    class extends ClientLine {
    /**
    * Calling the function when clicking click-order button from setup()
    */
        setup() {
            super.setup();
            useListener('click-order', this._onClickOrder);
            var self = this;
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
Registries.Component.extend(ClientListScreen, PosOrderPartnerLine);
return ClientListScreen;
});