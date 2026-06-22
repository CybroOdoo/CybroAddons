/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
import { patch } from "@web/core/utils/patch";
import { CarouselSlider } from "@website/interactions/carousel/carousel_slider";
import { CarouselProduct } from "@website_sale/interactions/carousel_product";

// Patch CarouselSlider to handle out-of-bounds thumbnails gracefully (e.g. 3D models)
patch(CarouselSlider.prototype, {
    prefetchImages(toLoadEls) {
        return super.prefetchImages(toLoadEls.filter(Boolean));
    }
});

// Patch CarouselProduct to handle slides without indicators gracefully (e.g. 3D models)
patch(CarouselProduct.prototype, {
    onSlideCarouselProduct(ev) {
        const isReversed = this.el.style["flex-direction"] === "column-reverse";
        const isLeftIndicators = this.el.classList.contains("o_carousel_product_left_indicators");
        const indicatorsDivEl = this.el.querySelector(isLeftIndicators ? ".o_carousel_product_indicators" : ".carousel-indicators");
        if (indicatorsDivEl) {
            const currentIndicatorEl = ev?.relatedTarget || this.el.querySelector("li.active");
            const indicatorIndex = currentIndicatorEl ? [...currentIndicatorEl.parentElement.children].findIndex(el => el === currentIndicatorEl) : -1;
            const indicatorEl = indicatorsDivEl.querySelector(`[data-bs-slide-to="${indicatorIndex}"]`);
            if (!indicatorEl) {
                // If there's no matching indicator, skip Odoo's indicator auto-scroll logic to prevent null pointer exceptions
                return;
            }
        }
        return super.onSlideCarouselProduct(ev);
    }
});

publicWidget.registry.product_detail_view_3d = publicWidget.Widget.extend({
    selector: '.o_wsale_product_page',
    events: {
        'click .product_images': '_arViewBtn',
        'slid.bs.carousel #o-carousel-product': '_onCarouselSlid',
    },

    /**
     * Called when Bootstrap carousel finishes sliding (mobile swipe or arrow nav).
     * Checks whether the newly active slide corresponds to the 3D model indicator
     * and shows/hides the AR model viewer accordingly.
     */
    _onCarouselSlid: function (ev) {
        var self = this;
        // Find the 3D indicator li element
        const $arIndicator = this.$('.product_images[data-type="3d"]');
        if (!$arIndicator.length) {
            return;
        }
        const arSlideIndex = parseInt($arIndicator.data('bs-slide-to'));
        // ev.to is the index of the newly active slide
        if (ev.to === arSlideIndex) {
            // Navigated to the 3D slide
            const productId = parseInt($arIndicator.attr('id'));
            this.$('.product_images').removeClass('active');
            $arIndicator.addClass('active');
            this._loadArModel(productId);
        } else {
            // Navigated away from 3D slide — restore carousel view
            this._hideArModel();
            // Sync thumbnail active state
            this.$('.product_images').removeClass('active');
            this.$('.product_images[data-bs-slide-to="' + ev.to + '"]').addClass('active');
        }
    },

    // Function to see the AR image of the product (triggered by thumbnail click)
    _arViewBtn: function (ev) {
        var self = this;
        ev.preventDefault();

        const $clickedThumb = this.$(ev.currentTarget);

        // Remove active class from all thumbnails and add to clicked one
        this.$('.product_images').removeClass('active');
        $clickedThumb.addClass('active');

        if ($clickedThumb.data('type') == "3d") {
            const productId = parseInt(ev.currentTarget.id);
            this._loadArModel(productId);
        } else {
            this._hideArModel();

            const $carousel = this.$('.o_carousel_product_outer');
            $carousel.removeClass('d-none').show();

            // Reinitialize Bootstrap carousel and sync to clicked slide
            const carouselElement = $carousel.find('.carousel')[0];
            if (carouselElement) {
                const slideIndex = parseInt($clickedThumb.data('bs-slide-to'));
                const bsCarousel = bootstrap.Carousel.getInstance(carouselElement) ||
                                  new bootstrap.Carousel(carouselElement, {
                                      interval: false // Disable auto-sliding
                                  });
                bsCarousel.to(slideIndex);
            }
        }
    },

    /**
     * Load the AR model viewer for the given product ID.
     * Hides the carousel and shows the model-viewer in #product_main.
     */
    _loadArModel: function (productId) {
        var self = this;

        // Stop and hide the carousel
        const $carousel = this.$('.o_carousel_product_outer');
        if ($carousel.length) {
            const carouselElement = $carousel.find('.carousel')[0];
            if (carouselElement) {
                const bsCarousel = bootstrap.Carousel.getInstance(carouselElement);
                if (bsCarousel) {
                    bsCarousel.dispose();
                }
            }
            $carousel.addClass('d-none');
        }

        this.$('#product_main').removeClass('d-none').show();

        rpc('/product/ar_image', {
            'product_id': productId,
        }).then(function(data) {
            self.data = data;

            var ar_image = data['type'] === 'url' ? data['ar_url'] : data['local_url'];
            const autoRotateAttribute = data['auto_rotate'] ? 'auto-rotate' : '';
            const placementAttribute = data['ar_placement'];
            const scaleAttribute = data['ar_scale'];

            self.$('#product_main').html(`
                <model-viewer id="model-viewer"
                    src="${ar_image}"
                    ar
                    ar-scale="${scaleAttribute}"
                    camera-controls
                    touch-action="pan-y"
                    ar-placement="${placementAttribute}"
                    alt="A 3D model of the product"
                    xr-environment
                    ${autoRotateAttribute}>
                    <button slot="ar-button" id="custom-ar-button" class="btn btn-primary">
                        View in AR
                    </button>
                </model-viewer>
            `);
        });
    },

    /**
     * Hide the AR model viewer and restore the standard carousel.
     */
    _hideArModel: function () {
        this.$('#product_main').hide().addClass('d-none');
        this.$('#product_main').html('');
    },
});

export default publicWidget.registry.product_detail_view_3d;