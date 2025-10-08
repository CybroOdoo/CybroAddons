odoo.define('customer_screen_pos.ProductItemClick', function (require) {
    "use strict";
    /**
    Function for generating customer screen when selecting a product to order
    lines
    */
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    var ajax = require('web.ajax');
    var encodedResult
    const ProductItemClick = (ProductScreen) => class ProductItemClick
        extends ProductScreen {
        /**
        In here we get order-line records from pos and pass to controller for
        creating template for customer screen using records,
        In ajax then function we get customer screen template body then we merge
        it with a demo template
        */
        async _clickProduct(event) {
            await super._clickProduct(event)
            if (this.env.pos.config.allow_product_click) {
                var self = this
                var total = 0
                var totalvalues = this.env.pos.selectedOrder.orderlines
                totalvalues.forEach(function (totalvalues) {
                    total = total + (totalvalues.price * totalvalues.quantity)
                })
                var orderlines = this.env.pos.get_order().orderlines;
                var orderlinelist = [];
                orderlines.forEach(function(orderline) {
                    // Perform operations with each orderline here
                    if (!orderlinelist.includes(orderline.product.display_name)) {
                        orderlinelist.push({
                            'id' : orderline.product.id,
                            'name' : orderline.product.display_name,
                            'price' : (orderline.price * orderline.quantity),
                            'qty' : orderline.quantity,
                            'session': self.env.pos.get_order().pos.pos_session.id,
                            'partner_id': self.env.pos.get_order().partner ? self.env.pos.get_order().partner.id : null,
                            'order_name': self.env.pos.get_order().name,
                            'total': total
                        });
                    }
                });
                ajax.jsonRpc('/add/my/review', 'call', {'orderlinelist': orderlinelist, 'total': total})
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
                            console.log('Error:', error);
                        });
                })
                return this.env.pos.get_order();
            }
        }
    }
    ProductItemClick.template = 'ShowProductImages';
    Registries.Component.extend(ProductScreen, ProductItemClick);
});
