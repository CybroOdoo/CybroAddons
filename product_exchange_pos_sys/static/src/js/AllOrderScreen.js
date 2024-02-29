odoo.define('product_exchange_pos_sys.all_order_screen', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require("@web/core/utils/hooks");
    const Registries = require('point_of_sale.Registries');
    const { Gui } = require('point_of_sale.Gui');
    var rpc = require('web.rpc');
    var core = require('web.core');

    class CustomOrdrScreen extends PosComponent {
        setup() {
            super.setup();
            useListener('click-order', this._onClickOrder);
            this.state = {
                order: this.props.orders,
                pos: this.env.pos
            };
        }
//        Going back to the product screen
        back() {
            this.showScreen('ProductScreen');
        }
//        Refresh window
        reload(){
            window.location.reload();
        }
//        Function for fetching all orders
        async _onClickOrder(order, pos) {
            if (order.is_exchange == true) {
                await Gui.showPopup('ErrorPopup', {
                    title: this.env._t('Exchange order'),
                    body: this.env._t('Already created the Exchange order')
                });
            } else {
                var lines = []
                var self = this;
                this.rpc({
                    model: 'pos.order.line',
                    method: 'get_product_details',
                    args: [order.lines],
                }).then(async function(value) {
                    for (var i = 0; i < self.state.order.length; i++) {
                        lines.push(self.state.order[i])
                    }
                    var _t = core._t;
                    await self.trigger('close-temp-screen');
                    Gui.showPopup("ExchangeOrder", {
                        title: _t("Exchange Order"),
                        cancelText: 'Cancel',
                        'order_line': value,
                    });
                });

            }
        }
    };
    CustomOrdrScreen.template = 'CustomOrdrScreen';
    Registries.Component.add(CustomOrdrScreen);
    return CustomOrdrScreen;
});
