/** @odoo-module */
import PublicWidget from "@web/legacy/js/public/public_widget"

export const aboutSlider = PublicWidget.Widget.extend({
    selector: "#wrapwrap",
    /* Start function for calling slider function */
    start() {
        this.about_carousel()
    },
    /*  Function for about page carousel slider */
    about_carousel() {
        if(this.$el.find("#owl-slider-8")){
            this.$el.find("#owl-slider-8").owlCarousel({
                items: 3,
                loop: true,
                margin: 40,
                stagePadding: 0,
                smartSpeed: 450,
                autoplay: true,
                autoPlaySpeed: 3000,
                autoPlayTimeout: 1000,
                autoplayHoverPause: true,
                dots: true,
                nav: true,
                animateIn: "fadeIn",
                animateOut: "fadeOut",
                center: true,
            })
        }
    },
})

PublicWidget.registry.aboutSlider = aboutSlider
