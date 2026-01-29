odoo.define('product_exchange_pos_sys.ExchangeOrder', function(require) {
    'use strict';

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');

    class ExchangeOrder extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
        }
//        Confirming the exchange returns to the product screen
        async confirm() {
            const CurrentOrder = this.env.pos.get_order()
            for (var i = 0; i < this.props.order_line.length; i++) {
                var order_id = this.props.order_line[i].order_id
                var product = this.env.pos.db.get_product_by_id(this.props.order_line[i].product_id)
                CurrentOrder.add_product(product, {
                    quantity: -this.props.order_line[i].qty
                })
            }
            this.rpc({
                model: 'pos.order',
                method: 'pos_exchange_order',
                args: [this.props.order_line[0].order_id],
            })
            this.showScreen('ProductScreen');
            super.confirm();
        }
    }
    ExchangeOrder.template = 'ExchangeOrder';
    ExchangeOrder.defaultProps = {
        confirmText: 'Ok',
        cancelText: 'Cancel',
        title: 'Confirm ?',
        body: '',
    };
    Registries.Component.add(ExchangeOrder);
    return ExchangeOrder;
});
