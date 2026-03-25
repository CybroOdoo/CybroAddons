/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.product_detail_view_3d = publicWidget.Widget.extend({
    selector: '.o_wsale_product_page',
    events: {
        'click .product_images': '_arViewBtn',
    },

    // Function to see the AR image of the product
    _arViewBtn: function (ev) {
        var self = this;
        ev.preventDefault();

        const $clickedThumb = this.$(ev.currentTarget);

        // Remove active class from all thumbnails and add to clicked one
        this.$('.product_images').removeClass('active');
        $clickedThumb.addClass('active');

        if ($clickedThumb.data('type') == "3d") {
            // Stop the carousel before hiding it
            const $carousel = this.$('.o_carousel_product_outer');
            if ($carousel.length) {
                // Dispose of Bootstrap carousel instance to prevent events
                const carouselElement = $carousel.find('.carousel')[0];
                if (carouselElement) {
                    const bsCarousel = bootstrap.Carousel.getInstance(carouselElement);
                    if (bsCarousel) {
                        bsCarousel.dispose(); // Clean up carousel instance
                    }
                }
                $carousel.addClass('d-none');
            }

            this.$('#product_main').removeClass('d-none').show();

            rpc('/product/ar_image', {
                'product_id': parseInt(ev.currentTarget.id),
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
        } else {
            // Reinitialize carousel when switching back
            this.$('#product_main').hide().addClass('d-none');

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
});

export default publicWidget.registry.product_detail_view_3d;