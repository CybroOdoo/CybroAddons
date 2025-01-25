/** @odoo-module */
import Animation from "@website/js/content/snippets.animation";

Animation.registry.shopping = Animation.Class.extend({
    selector : '.offer_snippet',
    start: function(){
    var self = this;
    self.offer_snippet_carousel();
    },
     offer_snippet_carousel: function () {
        var self= this;
        this.$("#offer_product_carousel").owlCarousel({
            items: 1,
            loop: true,
            nav: false,
            autoplay: true,
            dots: true,
        });
        },
        });
