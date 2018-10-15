odoo.define('point_of_sale.pos_product_image_magnify', function (require) {
"use strict";

var screens = require('point_of_sale.screens');
var gui = require('point_of_sale.gui');
var core = require('web.core');
var AbstractAction = require('web.AbstractAction')
var PopupWidget = require('point_of_sale.popups');
var ProductListWidget = screens.ProductListWidget;
var QWeb = core.qweb;
var _t = core._t;

ProductListWidget.include({
    renderElement: function() {
    var el_str  = QWeb.render(this.template, {widget: this});
    var el_node = document.createElement('div');
        el_node.innerHTML = el_str;
        el_node = el_node.childNodes[1];

    if(this.el && this.el.parentNode){
        this.el.parentNode.replaceChild(el_node,this.el);
        }
    this.el = el_node;
    var list_container = el_node.querySelector('.product-list');
    for(var i = 0, len = this.product_list.length; i < len; i++){
        var product_node = this.render_product(this.product_list[i]);
        product_node.addEventListener('click',this.click_product_handler);
        product_node.querySelector('.pos-product-magnify').addEventListener('click',this.on_click_pos_product_magnify);
        list_container.appendChild(product_node);
        }
    },
    get_product_image_large: function(product){
        return window.location.origin + '/web/image?model=product.product&field=image&id='+product.id;
    },

    on_click_pos_product_magnify: function (e) {
        var self = this;
        e.stopPropagation();
        var $target = $(e.currentTarget).parent();
        var product_id = $target.data('product-id');
        var product = this.pos.db.get_product_by_id(product_id);
        var image_url = this.get_product_image_large(product);
        this.gui.show_popup('product_image',{image_url:image_url, 'title': product.display_name});
    },
});

var ProductZoomPopupWidget = PopupWidget.extend({
    template: 'ProductZoomPopupWidget',
    show: function(options){
        options = options || {};
        var self = this;
        this._super(options);
        this.image_url    = options.image_url
        this.renderElement();
    }
});
gui.define_popup({name:'product_image', widget: ProductZoomPopupWidget});
});

