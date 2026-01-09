/** @odoo-module **/
import { Component, onMounted, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import PublicWidget from "@web/legacy/js/public/public_widget";

export const customFashion = PublicWidget.Widget.extend({
    selector: "#wrapwrap",

    // Create a ref for the banner element
    setup() {
        this.bannerRef = useRef("bannerElement");
        console.log(this.bannerRef);

        onMounted(() => {
            this.initBanner();
        });
    },

    initBanner() {
        const bannerElement = this.bannerRef.el;

        if (bannerElement) {
            $(bannerElement).owlCarousel({
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
            });
        }
    }
});

PublicWidget.registry.customFashion = customFashion;