odoo.define('all_in_one_pos_kit.ExchangeOrder', function(require) {
    'use strict';
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { useState } = owl;
    /**
    * Represents an Exchange Order popup in a point of sale system.
    * This class extends the AbstractAwaitablePopup class and provides functionality
    * for confirming an exchange order. The exchange order allows products to be
    * added or removed from the current order based on the provided order line.
    * @extends AbstractAwaitablePopup
    */
    class ExchangeOrder extends AbstractAwaitablePopup {
        setup() {// Super the setup function and set props.line and state.line
            super.setup();
            this.props.line = JSON.parse(JSON.stringify(this.props.order_line))
            this.state = useState({
                line: JSON.parse(JSON.stringify(this.props.order_line)),
                pos: this.props.pos
            });
        }
        async confirm() {// Iterate over each line in props.line and add or remove products from the CurrentOrder
            for(var i = 0; i < this.props.line.length; i++){
                this.env.pos.get_order().add_product(this.env.pos.db.get_product_by_id(this.props.line[i].product_id), {quantity: - this.props.line[i].qty})
                }
            this.rpc({// Perform a remote procedure call (RPC) to handle the exchange order on the server side
                   model: 'pos.order',
                   method: 'get_pos_exchange_order',
                   args: [this.props.order_id],
            })
            this.showScreen('ProductScreen');// Show the 'ProductScreen' and invoke the confirm method of the parent class
            super.confirm();
        }
    }
    ExchangeOrder.template = 'ExchangeOrder';
    ExchangeOrder.defaultProps = { cancelKey: false };
    Registries.Component.add(ExchangeOrder);
    return ExchangeOrder;
});
