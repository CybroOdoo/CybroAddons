/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";
import publicWidget from "@web/legacy/js/public/public_widget";
import { loadJS } from "@web/core/assets";

publicWidget.registry.popularProductCarousel = publicWidget.Widget.extend({
    selector: '.diva_popular_product',

    async start() {
        try {
            await this._loadCarouselAssets();
            await this._fetchAndRenderProducts();
            return publicWidget.Widget.prototype.start.apply(this, arguments);
        } catch (error) {
            console.error("Error starting popular product carousel:", error);
        }
    },

    async _loadCarouselAssets() {
        await loadJS("/theme_diva/static/src/js/owl.carousel.min.js");
    },

    async _fetchAndRenderProducts() {
        const products = await rpc("/popular/products");
        const carousel = this.el.querySelector('#owl-theme2');

        if (!carousel) return;

        carousel.innerHTML = '';
        carousel.classList.add('owl-carousel', 'owl-theme');

        products.forEach(product => {
            const variantText = product.variant_count === 1 ? 'Variant' : 'Variants';
            const card = document.createElement('div');
            card.className = 'item';
            card.innerHTML = `
                <div class="card">
                    <img class="card-img-top" src="${product.image_url}" alt="${product.name}"/>
                    <div class="card-body">
                        <div class="body_wrapp">
                            <h5 class="card-title">${product.name}</h5>
                            <p class="card-text">${product.description || ''}</p>
                        </div>
                        <div class="card-footer d-flex">
                            <div class="total">
                                <span>${product.variant_count} ${variantText}</span>
                                ${product.price ? `<span class="price">$${product.price.toFixed(2)}</span>` : ''}
                            </div>
                            <a href="${product.url}" class="btn btn-populor">
                                <i class="bi bi-arrow-right-short"></i>
                            </a>
                        </div>
                    </div>
                </div>
            `;
            carousel.appendChild(card);
        });

        this._initializeCarousel();
    },

    _initializeCarousel() {
        const $carousel = $(this.el).find("#owl-theme2");

        if ($carousel.length && $.fn.owlCarousel) {
            $carousel.owlCarousel({
                loop: true,
                margin: 30,
                nav: true,
                dots: true,
                smartSpeed: 600,
                autoplay: true,
                autoplayTimeout: 3000,
                responsive: {
                    0: { items: 1 },
                    768: { items: 2 },
                    992: { items: 3 }
                }
            });
        } else {
            console.warn("Carousel DOM missing or Owl not loaded.");
        }
    }
});