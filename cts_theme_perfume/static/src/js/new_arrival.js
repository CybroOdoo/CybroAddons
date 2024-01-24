/** @odoo-module **/

import { registry } from "@web/core/registry";
import animations from "@website/js/content/snippets.animation";

//Create a widget class for the snippet new arrival
animations.registry.NewArrival = animations.Class.extend({
     selector : '.NewArrivals',

     //Initialising rpc from bindService to this.rpc
     init() {
        this._super(...arguments);
        this.rpc = this.bindService("rpc");
     },
    /**In the start function we are fetching data from backend using rpc call
       and then the data is used in the snippet new arrival **/
    start: function(){
        var self = this;
        this.rpc('/get_arrival_product', {})
        .then(function (data) {
            if(data){
                self.$target.empty().append(data);
            }
        });
    }
});