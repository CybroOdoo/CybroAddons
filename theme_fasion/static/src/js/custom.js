/** @odoo-module */
import PublicWidget from "@web/legacy/js/public/public_widget"

export const customFasion = PublicWidget.Widget.extend({
    selector: "#wrapwrap",
    /* Start function for calling slider function */
    start() {
//        this.banner()
    },
    /*  Function for carousel slider */

    banner() {
        if(this.$el.find("#banner")){
            this.$el.find("#banner").owlCarousel(
                {
                    items: 1,
                    loop: true,
                    margin: 40,
                    stagePadding: 0,
                    smartSpeed: 450,
                    autoplay: false,
                    autoPlaySpeed: 1000,
                    autoPlayTimeout: 1000,
                    autoplayHoverPause: true,
                    dots: true,
                    nav: false,
                    animateOut: 'fadeOut'
                }
            )
        }
    },
})

PublicWidget.registry.customFasion = customFasion
