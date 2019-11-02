odoo.define('pos_rfid_payment.models', function (require) {
"use strict";
var screens = require('point_of_sale.screens');
var OrderWidget = screens.OrderWidget
var core = require('web.core');
var QWeb = core.qweb;

OrderWidget.include({
    render_orderline: function(orderline){
        var image_url = this.get_product_image_url(orderline.product);
        var el_str  = QWeb.render('Orderline',{widget:this, line:orderline, image_url:image_url});
        var el_node = document.createElement('div');
            el_node.innerHTML = _.str.trim(el_str);
            el_node = el_node.childNodes[0];
            el_node.orderline = orderline;
            el_node.addEventListener('click',this.line_click_handler);

        orderline.node = el_node;
        return el_node;
    },
    get_product_image_url: function(product){
        return window.location.origin + '/web/image?model=product.product&field=image_128&id='+product.id;
    },
});


});
