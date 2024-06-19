/**This module extends the functionality of Odoo's backend order handling in the context
 * of multi-currency transactions. It overrides the standard `_save_to_server` method
 * to accommodate multi-currency data and ensure that the converted currency values are
 * correctly saved to the server. */
odoo.define('backend_order.MultiCurrencyValues', function(require) {
    "use strict";
    const { PosGlobalState } = require('point_of_sale.models')
    const { useListener } = require("@web/core/utils/hooks");
    const Registries = require('point_of_sale.Registries');
    var rpc = require('web.rpc');
    const MultiCurrencyValues = PosGlobalState => class extends PosGlobalState {
        setup() {
            super.setup();
        }
        // OverRiding this function, Since it conflicts with other
        // Function when we Super this Function
        _save_to_server (orders, options) {
            if(orders.length > 0){
                for (let i = 0, len = orders[0].data.statement_ids.length; i < len; i++){
                    if(this.orders[0].paymentlines[i].converted_currency){
                        orders[0].data.statement_ids[i][2].currency_amount = this.orders[0].paymentlines[i].converted_currency.amount
                        orders[0].data.statement_ids[i][2].payment_currency = this.orders[0].paymentlines[i].converted_currency.name
                    }else{
                        orders[0].data.statement_ids[i][2].currency_amount = ""
                        orders[0].data.statement_ids[i][2].payment_currency = ""
                    }
                }
            }
            if (!orders || !orders.length) {
                return Promise.resolve([]);
            }
            this.set_synch('connecting', orders.length);
            options = options || {};
            var self = this;
            var timeout = typeof options.timeout === 'number' ? options.timeout : 30000 * orders.length;
            // Keep the order ids that are about to be sent to the
            // backend. In between create_from_ui and the success callback
            // new orders may have been added to it.
            var order_ids_to_sync = _.pluck(orders, 'id');
            // We try to send the order. shadow prevents a spinner if it takes too long. (unless we are sending an invoice,
            // then we want to notify the user that we are waiting on something )
            var args = [_.map(orders, function (order) {
                    order.to_invoice = options.to_invoice || false;
                    return order;
                })];
            args.push(options.draft || false);
            return this.env.services.rpc({
                    model: 'pos.order',
                    method: 'create_from_ui',
                    args: args,
                    kwargs: {context: this.env.session.user_context},
                }, {
                    timeout: timeout,
                    shadow: !options.to_invoice
                })
                .then(function (server_ids) {
                    _.each(order_ids_to_sync, function (order_id) {
                        self.db.remove_order(order_id);
                    });
                    self.failed = false;
                    self.set_synch('connected');
                    return server_ids;
                }).catch(function (error){
                    console.warn('Failed to send orders:', orders);
                    if(error.code === 200 ){    // Business Logic Error, not a connection problem
                        // Hide error if already shown before ...
                        if ((!self.failed || options.show_error) && !options.to_invoice) {
                            self.failed = error;
                            self.set_synch('error');
                            throw error;
                        }
                    }
                    self.set_synch('disconnected');
                    throw error;
        });
    }
    }
    Registries.Model.extend(PosGlobalState, MultiCurrencyValues);
    return MultiCurrencyValues;
});
