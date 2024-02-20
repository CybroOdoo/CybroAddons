/** @odoo-module **/

var PublicWidget = require('web.public.widget');
var core = require('web.core');
PublicWidget.registry.eco_client = PublicWidget.Widget.extend({
    selector: '.eco-clients',
    disabledInEditableMode: false,
    start: function() {
        var self = this;
        var QWeb = core.qweb;
        this.onSlider();
    },
    onSlider: function() {
        let slider = this.$el.find(".client-carousel");
        slider.owlCarousel(
        {
            items: 5,
            loop: true,
            margin: 40,
            stagePadding: 0,
            smartSpeed: 450,
            autoplay: false,
            autoPlaySpeed: 3000,
            autoPlayTimeout: 1000,
            autoplayHoverPause: true,
            dots: false,
            nav: true,
        }
    );
    },
    destroy: function () {
            this._clearContent();
            this._super.apply(this, arguments);
    },
    _clearContent: function () {
        const $templateArea = this.$el.find('.eco-clients');
        this.trigger_up('widgets_stop_request', {
            $target: $templateArea,
        });
        $templateArea.html('');
    },
});