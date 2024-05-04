/** @odoo-module */
import { Navbar } from "@point_of_sale/app/navbar/navbar";
import { jsonrpc } from "@web/core/network/rpc_service";
import { patch } from "@web/core/utils/patch";

patch(Navbar.prototype, {
        onClick() {
            var self = this;
            var total = 0
            var totalvalues = this.pos.selectedOrder.orderlines
            totalvalues.forEach(function (totalvalues) {
                total = total + (totalvalues.price * totalvalues.quantity)
            })
            var orderlines = this.pos.selectedOrder.orderlines
            var orderlinelist = [];
            orderlines.forEach(function(orderline) {
                // Perform operations with each orderline here
                if (!orderlinelist.includes(orderline.product.display_name)) {
                    orderlinelist.push({
                        'id' : orderline.product.id,
                        'name' : orderline.product.display_name,
                        'price' : (orderline.price * orderline.quantity),
                        'qty' : orderline.quantity,
                        'session': self.pos.selectedOrder.pos_session_id,
                        'partner_id': self.pos.selectedOrder.partner ? self.pos.selectedOrder.partner.id : null,
                        'order_name': self.pos.selectedOrder.name,
                        'total': total
                    });
                }
            });
           jsonrpc('/add/my/review', {'orderlinelist': orderlinelist, 'total': total})
            .then(function (result) {
                var encodedResult = result
                var url = "/customer/screen/";
                fetch(url)
                    .then(function (response) {
                        return response.text();
                    })
                .then(function (data) {
                    var modifiedData = data.replace('<body>', '<body>' + encodedResult);
                    var newWindow = window.open("", 'Customer Display Screen', 'height=500,width=900');
                    newWindow.document.open();
                    newWindow.document.write(modifiedData);
                    newWindow.document.close();
                })
                .catch(function (error) {
                });
            })
            return this.pos.selectedOrder;
        }
    });
