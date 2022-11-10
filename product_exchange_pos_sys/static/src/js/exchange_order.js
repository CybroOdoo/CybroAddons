odoo.define('product_exchange_pos_sys.ExchangeOrder', function(require) {
    'use strict';

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { useState } = owl;

    class ExchangeOrder extends AbstractAwaitablePopup {
        setup() {
            super.setup();
            this.props.line = JSON.parse(JSON.stringify(this.props.order_line))
            this.state = useState({
                line: JSON.parse(JSON.stringify(this.props.order_line)),
                pos: this.props.pos
            });
        }
        //@override
        async confirm() {
            const CurrentOrder = this.env.pos.get_order()
            for(var i = 0; i < this.props.line.length; i++){
                var product = this.env.pos.db.get_product_by_id(this.props.line[i].product_id)
                CurrentOrder.add_product(product, {quantity: - this.props.line[i].qty})
                }
            this.rpc({
                   model: 'pos.order',
                   method: 'pos_exchange_order',
                   args: [this.props.order_id],
            })
            this.showScreen('ProductScreen');
            super.confirm();
        }
    }

    ExchangeOrder.template = 'ExchangeOrder';
    ExchangeOrder.defaultProps = { cancelKey: false };
    Registries.Component.add(ExchangeOrder);

    return ExchangeOrder;
});