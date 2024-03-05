/** @odoo-module **/

import { registry } from "@web/core/registry";
import animations from "@website/js/content/snippets.animation";

animations.registry.get_blog_post = animations.Class.extend({
 selector : '.blog',

     //Initialising rpc from bindService to this.rpc
     init() {
        this._super(...arguments);
        this.rpc = this.bindService("rpc");
     },

    //Get blog related data from specified route '/get_blog_post' and append it
    start: function(){
        var self = this;
        this.rpc('/get_blog_post', {})
        .then(function (data) {
            if(data){
                self.$target.empty().append(data);
            }
        });
    }
});

 animations.registry.get_main_product = animations.Class.extend({
    selector : '.product',

    //Initialising rpc from bindService to this.rpc
     init() {
        this._super(...arguments);
        this.rpc = this.bindService("rpc");
     },

     //Get product related data from specified route '/get_main_product'
     start: function(){
        var self = this;
        this.rpc("/get_main_product", {
        }).then((data) => {
            if(data){
                self.$target.empty().append(data);
            }
        });
     }
});
