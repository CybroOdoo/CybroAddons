/** @odoo-module **/

    /**
    Function for generating customer screen when selecting a product to order
    lines
    */
import { patch } from "@web/core/utils/patch";
import { Order } from "@point_of_sale/app/store/models";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { jsonrpc } from "@web/core/network/rpc_service";
var encodedResult

patch(PosStore.prototype, {
        /**
        In here we get order-line records from pos and pass to controller for
        creating template for customer screen using records,
        In ajax then function we get customer screen template body then we merge
        it with a demo template
        */
        async addProductToCurrentOrder(product, options = {}) {
        await super.addProductToCurrentOrder(product, options = {})

        var self = this
        var total = 0
        var totalvalues = self.selectedOrder.orderlines
        totalvalues.forEach(function (totalvalues) {
            total = total + (totalvalues.price * totalvalues.quantity)})
        var orderlines = this.selectedOrder.orderlines
        var orderlinelist = [];
        orderlines.forEach(function(orderline) {

                    // Perform operations with each orderline here
            if (!orderlinelist.includes(orderline.product.display_name)) {
                orderlinelist.push({
                    'id' : orderline.product.id,
                    'name' : orderline.product.display_name,
                    'price' : (orderline.price * orderline.quantity),
                    'qty' : orderline.quantity,
                    'session': self.selectedOrder.pos_session_id,
                    'partner_id': self.selectedOrder.partner ? self.selectedOrder.partner.id : null,
                    'order_name': self.selectedOrder.name,
                    'total': total
                });
            }
            });
             jsonrpc('/add/my/review', {'orderlinelist': orderlinelist, 'total': total})
             .then(function (result) {
                    encodedResult = result
                    var url = "/customer/screen/";
                    fetch(url)
                        .then(function (response) {
                            return response.text();
                        })
                        .then(function (data) {
                            var modifiedData = data.replace('<body>', '<body>' + encodedResult + '</body>');
                            var newWindow = window.open("", 'Customer Display Screen', 'height=500,width=900');
                            newWindow.document.open();
                            newWindow.document.write(modifiedData);
                            newWindow.document.close();
                        })
                        .catch(function (error) {
                        });
                })
                return this.selectedOrder;
        }
});
