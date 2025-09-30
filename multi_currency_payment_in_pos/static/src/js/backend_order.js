///** @odoo-module **/
///**This module extends the functionality of Odoo's backend order handling in the context
// * of multi-currency transactions. It overrides the standard `_save_to_server` method
// * to accommodate multi-currency data and ensure that the converted currency values are
// * correctly saved to the server. */
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { Payment } from "@point_of_sale/app/store/models";
patch(PosStore.prototype, {
async _save_to_server(orders, options) {
        if(orders.length > 0){
            for (let i = 0, len = orders[0].data.statement_ids.length; i < len; i++){
                if (this.orders[0].paymentlines[i]){
                    if(this.orders[0].paymentlines[i].converted_currency){
                        orders[0].data.statement_ids[i][2].currency_amount = this.orders[0].paymentlines[i].converted_currency.amount
                        orders[0].data.statement_ids[i][2].payment_currency = this.orders[0].paymentlines[i].converted_currency.name
                    }else{
                        orders[0].data.statement_ids[i][2].currency_amount = ""
                        orders[0].data.statement_ids[i][2].payment_currency = ""
                    }
                }
            }
        }
        if (!orders || !orders.length) {
            return Promise.resolve([]);
        }

        // Filter out orders that are already being synced
        const ordersToSync = orders.filter(order => !this.syncingOrders.has(order.id));

        if (!ordersToSync.length) {
            return Promise.resolve([]);
        }

        // Add these order IDs to the syncing set
        ordersToSync.forEach(order => this.syncingOrders.add(order.id));

        this.set_synch("connecting", ordersToSync.length);
        options = options || {};

        // Keep the order ids that are about to be sent to the
        // backend. In between create_from_ui and the success callback
        // new orders may have been added to it.
        const order_ids_to_sync = ordersToSync.map((o) => o.id);

        for (const order of ordersToSync) {
            order.to_invoice = options.to_invoice || false;
        }
        // we try to send the order. silent prevents a spinner if it takes too long. (unless we are sending an invoice,
        // then we want to notify the user that we are waiting on something )
        const orm = options.to_invoice ? this.orm : this.orm.silent;

        try {
            // FIXME POSREF timeout
            // const timeout = typeof options.timeout === "number" ? options.timeout : 30000 * orders.length;
            const serverIds = await orm.call(
                "pos.order",
                "create_from_ui",
                [ordersToSync, options.draft || false],
                {
                    context: this._getCreateOrderContext(ordersToSync, options),
                }
            );

            for (const serverId of serverIds) {
                const order = this.env.services.pos.orders.find(
                    (order) => order.name === serverId.pos_reference
                );

                if (order) {
                    order.server_id = serverId.id;
                }
            }

            for (const order_id of order_ids_to_sync) {
                this.db.remove_order(order_id);
            }

            this.failed = false;
            this.set_synch("connected");
            return serverIds;
        } catch (error) {
            console.warn("Failed to send orders:", ordersToSync);
            if (error.code === 200) {
                // Business Logic Error, not a connection problem
                // Hide error if already shown before ...
                if ((!this.failed || options.show_error) && !options.to_invoice) {
                    this.failed = error;
                    this.set_synch("error");
                    throw error;
                }
            }
            this.set_synch("disconnected");
            throw error;
        } finally {
            order_ids_to_sync.forEach(order_id => this.syncingOrders.delete(order_id));
        }
    }
})
patch(Payment.prototype, {
    export_for_printing() {
        const result = super.export_for_printing(...arguments);
        if(this.converted_currency){
            result.converted_currency_amount = this.converted_currency.amount
            result.converted_currency_name = this.converted_currency.name
            result.converted_currency_symbol = this.converted_currency.symbol
            this.currency_amount = this.converted_currency.amount
        }
        return result;
    },

});
