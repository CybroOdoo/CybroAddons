/** @odoo-module **/
import { jsonrpc } from "@web/core/network/rpc_service";
import Animation from "@website/js/content/snippets.animation";
/**
 * Defines an animation class for the arrivals element in the HTML document.
 * Sends an AJAX request to the /get_arrival_product URL using the ajax.jsonRpc
 * method, and calls the 'call' method on the server-side. If the request is successful,
 * @extends Animation.Class
 */

Animation.registry.arrival_product = Animation.Class.extend({
    selector : '.arrivals',
    start: function(){
        var self = this;
        return jsonrpc('/get_arrival_product', {
        }).then(function (data) {
            if(data){
                self.$target.empty().append(data);
            }
        });
    }
});
