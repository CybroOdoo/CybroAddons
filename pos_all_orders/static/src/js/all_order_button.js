odoo.define('pos_all_orders.ALLOrderLine', function (require) {
'use strict';
   const PosComponent = require('point_of_sale.PosComponent');
   const ProductScreen = require('point_of_sale.ProductScreen');
   const { useListener } = require("@web/core/utils/hooks");
   const Registries = require('point_of_sale.Registries');

   class ALLOrderLine extends PosComponent {
    setup() {
        super.setup();
        useListener('click', this.onClick);
    }
    /**
     * The function for clicking all order button for viewing all
        orders based on the condition set in configuration
     */
    onClick() {
        var session = this.env.pos.config.current_session_id[0]
        var self = this;
        this.rpc({
            model: 'pos.session',
            method: 'get_all_order_config',
            args: [
                []
            ],
        }).then(function(result) {
            if (result.config == 'current_session') {
                self.rpc({
                    model: 'pos.session',
                    method: 'get_all_order',
                    args: [
                        [], {
                            session: session
                        }
                    ],
                }).then(function(order) {
                    self.showScreen('CustomALLOrdrScreen', {
                        orders: order,
                        pos: self.env.pos
                    });
                });
            } else if (result.config == 'past_order') {
                self.showScreen('CustomALLOrdrScreen', {
                    orders: self.env.pos.pos_orders,
                    pos: self.env.pos
                });
            } else if (result.config == 'last_n') {
                self.rpc({
                    model: 'pos.session',
                    method: 'get_all_order',
                    args: [
                        [], {
                            session: session,
                            no_of_days: result.no_of_days
                        }
                    ],
                }).then(function(order) {
                    self.showScreen('CustomALLOrdrScreen', {
                        orders: order,
                        pos: self.env.pos
                    });
                });
            } else {
                self.showScreen('CustomALLOrdrScreen', {
                    orders: self.env.pos.pos_orders,
                    pos: self.env.pos
                });
            }
        });
    }
}
ALLOrderLine.template = 'ALLOrderLine';
ProductScreen.addControlButton({
    component: ALLOrderLine,
    condition: function() {
        return true;
    },
    position: ['before', 'SetPricelistButton'],
});
Registries.Component.add(ALLOrderLine);
return ALLOrderLine;
});