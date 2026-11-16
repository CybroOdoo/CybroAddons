import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class HomeBanner extends Interaction {
    static selector = ".home_banner";

    start() {
        this.mountCarousels();
        this.animateImages();
    }

    mountCarousels() {
        const mainEl = this.el.querySelector(".main_carousel");
        const thumbnailEl = this.el.querySelector(".thumbnail_carousel");
        if (!mainEl || !thumbnailEl) {
            return;
        }
        const mainCarousel = new Splide(mainEl, {
            type: "fade",
            rewind: true,
            pagination: false,
            arrows: false,
        });
        const thumbnailCarousel = new Splide(thumbnailEl, {
            fixedWidth: 100,
            gap: 10,
            rewind: true,
            pagination: false,
            isNavigation: true,
            arrows: false,
        });
        mainCarousel.sync(thumbnailCarousel);
        mainCarousel.mount();
        thumbnailCarousel.mount();
        this.registerCleanup(() => {
            mainCarousel.destroy();
            thumbnailCarousel.destroy();
        });
    }

    animateImages() {
        const images = this.el.querySelectorAll(".rotating-image");
        if (!images.length) {
            return;
        }
        gsap.registerPlugin(ScrollTrigger);
        gsap.set(images, { rotationY: -180 });
        const tween = gsap.to(images, {
            scrollTrigger: {
                trigger: images[0],
                scroller: document.querySelector("#wrapwrap"),
                start: "top center",
                end: "bottom center",
                scrub: true,
            },
            rotationY: 180,
            ease: "none",
        });
        this.registerCleanup(() => {
            tween.scrollTrigger?.kill();
            tween.kill();
            gsap.set(images, { clearProps: "transform" });
        });
    }
}

registry.category("public.interactions").add("theme_voltro.home_banner", HomeBanner);
