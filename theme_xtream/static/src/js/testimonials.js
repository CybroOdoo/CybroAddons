/** @odoo-module **/
import { jsonrpc } from "@web/core/network/rpc_service";
import Animation from "@website/js/content/snippets.animation";
/**
 * Defines an animation class for the arrivals element in the HTML document.
 * Sends an AJAX request to the /get_testimonials URL using the ajax.jsonRpc
 * method, and calls the 'call' method on the server-side. If the request is successful,
 * @extends Animation.Class
 */

Animation.registry.testimonial_xtream = Animation.Class.extend({
    selector : '.testimonial_xtream',
    start: function(){
        var self = this;
        return jsonrpc('/get_testimonials', {
        }).then(function (data) {
            if(data){
                self.$target.empty().append(data);
            }
            self.$target.find('#slider2').owlCarousel(
                {
                    items: 1,
                    loop: true,
                    smartSpeed: 450,
                    autoplay: true,
                    autoPlaySpeed: 1000,
                    autoPlayTimeout: 1000,
                    autoplayHoverPause: true,
                    onInitialized: self.counter,
                    dots: true,
                }
            );
        });
    },
    counter() {
        var buttons = $('.owl-dots button');
        buttons.each(function (item) {
        });
    },
});
