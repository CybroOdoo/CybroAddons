import { Interaction } from "@web/public/interaction";
import { rpc } from "@web/core/network/rpc";
import { patch } from "@web/core/utils/patch";
import { CarouselSlider } from "@website/interactions/carousel/carousel_slider";
import { CarouselProduct } from "@website_sale/interactions/carousel_product";
import { registry } from "@web/core/registry";

// Patch CarouselSlider to handle out-of-bounds thumbnails gracefully (e.g. 3D models)
patch(CarouselSlider.prototype, {
    prefetchImages(toLoadEls) {
        return super.prefetchImages(toLoadEls.filter(Boolean));
    },
});

// Patch CarouselProduct to handle slides without indicators gracefully (e.g. 3D models)
patch(CarouselProduct.prototype, {
    onSlideCarouselProduct(ev) {
        const isLeftIndicators = this.el.classList.contains("o_carousel_product_left_indicators");
        const indicatorsDivEl = this.el.querySelector(
            isLeftIndicators ? ".o_carousel_product_indicators" : ".carousel-indicators"
        );
        if (indicatorsDivEl) {
            const currentIndicatorEl = ev?.relatedTarget || this.el.querySelector("li.active");
            const indicatorIndex = currentIndicatorEl
                ? [...currentIndicatorEl.parentElement.children].findIndex((el) => el === currentIndicatorEl)
                : -1;
            const indicatorEl = indicatorsDivEl.querySelector(`[data-bs-slide-to="${indicatorIndex}"]`);
            if (!indicatorEl) {
                // Skip Odoo auto-scroll if no indicator matches 3D model slide
                return;
            }
        }
        return super.onSlideCarouselProduct(ev);
    },
});

export class ProductDetailView3d extends Interaction {
    static selector = ".o_wsale_product_page";
    dynamicContent = {
        ".product_images": {
            "t-on-click": this._arViewBtn,
        },
        "#o-carousel-product": {
            "t-on-slid.bs.carousel": this._onCarouselSlid,
        },
    };

    /**
     * Called when Bootstrap carousel finishes sliding (mobile swipe or arrow nav).
     * Checks whether the newly active slide corresponds to the 3D model indicator
     * and shows/hides the AR model viewer accordingly.
     */
    _onCarouselSlid(ev) {
        const arIndicator = this.el.querySelector('.product_images[data-type="3d"]');
        if (!arIndicator) {
            return;
        }
        const arSlideIndex = parseInt(
            arIndicator.dataset.bsSlideTo || arIndicator.getAttribute("data-bs-slide-to")
        );
        if (ev.to === arSlideIndex) {
            const productId = parseInt(arIndicator.id);
            this.el.querySelectorAll(".product_images").forEach((el) => el.classList.remove("active"));
            arIndicator.classList.add("active");
            this._loadArModel(productId);
        } else {
            this._hideArModel();
            this.el.querySelectorAll(".product_images").forEach((el) => el.classList.remove("active"));
            const targetThumb = this.el.querySelector(`.product_images[data-bs-slide-to="${ev.to}"]`);
            if (targetThumb) {
                targetThumb.classList.add("active");
            }
        }
    }

    /**
     * Function to see the AR image of the product (triggered by thumbnail click).
     */
    _arViewBtn(ev) {
        ev.preventDefault();
        const clickedThumb = ev.currentTarget;

        this.el.querySelectorAll(".product_images").forEach((el) => el.classList.remove("active"));
        clickedThumb.classList.add("active");

        const dataType = clickedThumb.dataset.type || clickedThumb.getAttribute("data-type");
        if (dataType === "3d") {
            const productId = parseInt(clickedThumb.id);
            this._loadArModel(productId);
        } else {
            this._hideArModel();

            const carouselOuter = this.el.querySelector(".o_carousel_product_outer");
            if (carouselOuter) {
                carouselOuter.classList.remove("d-none");
                carouselOuter.style.display = "";

                const carouselElement = carouselOuter.querySelector(".carousel");
                if (carouselElement) {
                    const slideIndex = parseInt(
                        clickedThumb.dataset.bsSlideTo || clickedThumb.getAttribute("data-bs-slide-to")
                    );
                    const Carousel = window.Carousel || window.bootstrap?.Carousel;
                    if (Carousel) {
                        const bsCarousel =
                            Carousel.getInstance(carouselElement) ||
                            new Carousel(carouselElement, {
                                interval: false,
                            });
                        bsCarousel.to(slideIndex);
                    }
                }
            }
        }
    }

    /**
     * Load the AR model viewer for the given product ID.
     * Safely constructs DOM elements without innerHTML injection.
     */
    async _loadArModel(productId) {
        const carouselOuter = this.el.querySelector(".o_carousel_product_outer");
        if (carouselOuter) {
            const carouselElement = carouselOuter.querySelector(".carousel");
            if (carouselElement) {
                const Carousel = window.Carousel || window.bootstrap?.Carousel;
                if (Carousel) {
                    const bsCarousel = Carousel.getInstance(carouselElement);
                    if (bsCarousel) {
                        bsCarousel.dispose();
                    }
                }
            }
            carouselOuter.classList.add("d-none");
        }

        const productMain = this.el.querySelector("#product_main");
        if (productMain) {
            productMain.classList.remove("d-none");
            productMain.style.display = "block";
        }

        const data = await this.waitFor(
            rpc("/product/ar_image", {
                product_id: productId,
            })
        );

        if (!productMain) {
            return;
        }

        productMain.replaceChildren();

        const arImage = data?.type === "url" ? data.ar_url : data?.local_url;
        if (!arImage) {
            return;
        }

        const modelViewer = document.createElement("model-viewer");
        modelViewer.id = "model-viewer";
        modelViewer.setAttribute("src", arImage);
        modelViewer.setAttribute("ar", "");
        modelViewer.setAttribute("ar-scale", data.ar_scale || "auto");
        modelViewer.setAttribute("camera-controls", "");
        modelViewer.setAttribute("touch-action", "pan-y");
        modelViewer.setAttribute("ar-placement", data.ar_placement || "floor");
        modelViewer.setAttribute("alt", "A 3D model of the product");
        modelViewer.setAttribute("xr-environment", "");
        if (data.auto_rotate) {
            modelViewer.setAttribute("auto-rotate", "");
        }

        const arBtn = document.createElement("button");
        arBtn.setAttribute("slot", "ar-button");
        arBtn.id = "custom-ar-button";
        arBtn.className = "btn btn-primary";
        arBtn.textContent = "View in AR";

        modelViewer.appendChild(arBtn);
        productMain.appendChild(modelViewer);
    }

    /**
     * Hide the AR model viewer and restore standard carousel.
     */
    _hideArModel() {
        const productMain = this.el.querySelector("#product_main");
        if (productMain) {
            productMain.style.display = "none";
            productMain.classList.add("d-none");
            productMain.replaceChildren();
        }
    }
}

registry.category("public.interactions").add(
    "website_webar_product.product_detail_view_3d",
    ProductDetailView3d
);