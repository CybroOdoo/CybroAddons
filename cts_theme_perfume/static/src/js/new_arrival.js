/** @odoo-module **/

import { registry } from "@web/core/registry";
import { renderToElement } from "@web/core/utils/render";
import { rpc } from "@web/core/network/rpc";
import animations from "@website/js/content/snippets.animation";

//Create a widget class for the snippet new arrival
animations.registry.NewArrival = animations.Class.extend({
     selector : '.NewArrivals',

     //Initialising rpc from bindService to this.rpc
     init() {
        this._super(...arguments);
        this.rpc = rpc;
     },
    /**In the start function we are fetching data from backend using rpc call
       and then the data is used in the snippet new arrival **/
    start: function(){
        var self = this;
        const dataSet = this.el.dataset;

        this.rpc('/get_arrival_product', { products_count: dataSet['productsCount']})
        .then(function (data) {
            if(data){
                console.log($(self.el).find('.dynamic-snippet-content'), "@@", data)
                const area = $(self.el).find('.dynamic-snippet-content')
                // area.empty()
                area.empty().html(renderToElement('cts_theme_perfume.NewArrival', {products: data.products, currency: data.currency}))
                // area.append(data);
            }
        });
    }
});