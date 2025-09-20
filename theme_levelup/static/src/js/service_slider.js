/** @odoo-module */
import PublicWidget from "@web/legacy/js/public/public_widget"

export const serviceSlider = PublicWidget.Widget.extend({
    selector: "#wrapwrap",
    /* Start function for calling slider function */
    start() {
        this.slider_2()
    },
    /*  Function for carousel slider */
    slider_2() {
        if(this.$el.find('.test_slider2')){
            var owl = this.$el.find('.test_slider2').owlCarousel({
                loop: true,
                margin: 10,
                nav: false,
                dots:false,
                items: 3,
                center:true,
            })
            this.$el.find('.custom-nav .prev').click(function () {
                owl.trigger('prev.owl.carousel')
            })
            this.$el.find('.custom-nav .next').click(function () {
                owl.trigger('next.owl.carousel')
            });
        }
    },
})

PublicWidget.registry.serviceSlider = serviceSlider
