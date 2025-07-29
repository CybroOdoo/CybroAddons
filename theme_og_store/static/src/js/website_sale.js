/** @odoo-module */

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
import wSaleUtils from '@website_sale/js/website_sale_utils';


publicWidget.registry.BestSeller = publicWidget.Widget.extend({
    selector : '.o_wsale_products_main_row',

    events: {
        'click #load-more-btn': 'onClickLoadMore',
        'click .o_add_to_fav_website': '_onAddToFav',
        'click .cart-btn': '_onAddToCart',
    },

    start() {
        this._super(...arguments);
        this.currentProductCount = 12;
        this._initializeCarousel();
        this._recommendedCarousel();
        this._allCarousel();
    },

     _onAddToFav: function (ev) {
        const $btn = $(ev.currentTarget);
        const productId = $btn.data('product-id');
    },

    async _onAddToCart(ev) {
        ev.preventDefault();

        const $button = $(ev.currentTarget);
        const productId = $button.data('product-id');

        if (!productId) {
            console.error('Product ID not found on cart button');
            return;
        }

        try {
            // Use the correct RPC format for Odoo 16+
            const result = await rpc('/shop/cart/update_json', {
                product_id: productId,
                add_qty: 1
            });

            // Update the cart UI
            if (result) {
                // Update cart counter if it exists
                const $quantity = $(".my_cart_quantity");
                if ($quantity.length) {
                    $quantity.text(result.cart_quantity || 0);
                }

                // Show animation if available
                if (wSaleUtils) {
                    wSaleUtils.animateClone($('#wrapwrap'), $button, $quantity, 25, 40);
                } else {
                    // Simple visual feedback if animation not available
                    $button.addClass('added-to-cart');
                    setTimeout(() => {
                        $button.removeClass('added-to-cart');
                    }, 1000);
                }
            }
        } catch (error) {
            console.error('Failed to add product to cart:', error);
        }
    },

    onClickLoadMore(ev) {
        const allProductsSection = this.el.querySelector('.all-products-section');

        // Parse all products from the data attribute
        const products = JSON.parse(allProductsSection.getAttribute('data-all-products').replace(/'/g, '"'));

        // Extract product IDs to check for attributes
        const productIds = products.map(p => p.product_id);

        // Since we know the first 12 products are already displayed, let's use 12 as our starting point
        const productsPerPage = 12;

        // Check if there are more products to load
        if (this.currentProductCount >= products.length) {
            // You can also hide the load more button here
            ev.target.style.display = 'none';
            return;
        }

        // Get the next set of products (products 13-24)
        const nextProducts = products.slice(this.currentProductCount, this.currentProductCount + productsPerPage);

        // Function to continue with rendering after attributes are checked
        const continueWithRendering = () => {
            // Create a new section for the next products
            const newSection = document.createElement('section');
            newSection.className = 'best_seller';
            newSection.style.paddingLeft = '70px';

            const newCol = document.createElement('div');
            newCol.className = 'col-lg-12';

            const newCarousel = document.createElement('div');
            newCarousel.className = 'owl-carousel owl-theme';

            nextProducts.forEach((product) => {
                const productHTML = `
                    <div class="item">
                        <a href="${product.url}">
                            <div class="img-product">
                                <img src="${product.image_url}" alt="Product Image"/>
                            </div>
                            <div class="p-3 product-content">
                                <h6 class="text-dark mt-2">${product.name}</h6>
                                <h3 class="price-product"><b>${product.currency_symbol} ${parseFloat(product.price).toFixed(1)}</b></h3>
                                <div class="ratingandcart">
                                    <div class="container-rating">
                                        <a href="#" class="cart-btn" data-product-id="${product['product_variant_id']}">
                                            <img class="w-50" src="/theme_og_store/static/src/img/products/cart-icon.svg" alt="Cart Icon"/>
                                        </a>
                                    </div>
                                    <button class="btn btn-light o_add_wishlist"
                                        type="button"
                                        data-product-template-id="${product['product_id']}"
                                        data-product-product-id="${product['product_variant_id']}"
                                        id="${product.id}"
                                        role="button">
                                        <i class="fa fa-heart"></i>
                                    </button>
                                    ${product['product_variant_id'] && product['has_attributes'] ?
                                      `<button class="d-none d-md-inline-block btn btn-light o_add_compare"
                                        type="button"
                                        role="button"
                                        aria-label="Compare"
                                        id="${product.id}"
                                        data-product-product-id="${product['product_variant_id']}"
                                        data-action="o_comparelist">
                                        <i class="fa fa-exchange"></i>
                                      </button>` : ''}
                                </div>
                            </div>
                        </a>
                    </div>
                `;
                newCarousel.innerHTML += productHTML;
            });

            newCol.appendChild(newCarousel);
            newSection.appendChild(newCol);

            // Append the new section to the main container
            const mainContainer = document.querySelector('.all-products-section') || document.body;
            mainContainer.appendChild(newSection);

            // CRITICAL: Re-attach event handlers to the newly added cart buttons
            this._attachEventHandlersToNewProducts(newSection);

            // Initialize owl carousel for the new section if needed
            if (typeof $ !== 'undefined' && $.fn.owlCarousel) {
                $(newCarousel).owlCarousel({
                    // Your owl carousel options here
                    items: 4,
                    loop: true,
                    margin: 10,
                    nav: true,
                    responsive: {
                        0: { items: 1 },
                        600: { items: 2 },
                        1000: { items: 4 }
                    }
                });
            }

            // Update the current product count
            this.currentProductCount += nextProducts.length;

            // Hide load more button if no more products
            if (this.currentProductCount >= products.length) {
                ev.target.style.display = 'none';
            }
        };

        continueWithRendering();
    },

    // Add this new method to re-attach event handlers
    _attachEventHandlersToNewProducts(container) {
        // Re-attach cart button event handlers
        const cartButtons = container.querySelectorAll('.cart-btn');
        cartButtons.forEach(button => {
            button.addEventListener('click', this._onAddToCart);
        });

        // Re-attach wishlist button event handlers if you have them
        const wishlistButtons = container.querySelectorAll('.o_add_wishlist');
        wishlistButtons.forEach(button => {
            button.addEventListener('click', this._onAddToWishlist);
        });

        // Re-attach compare button event handlers if you have them
        const compareButtons = container.querySelectorAll('.o_add_compare');
        compareButtons.forEach(button => {
            button.addEventListener('click', this._onAddToCompare);
        });
    },


    _initializeCarousel() {
        const $slider = this.$('#carousel-1');
        if (!$slider.length) return;

        // Initialize Owl Carousel
        $slider.owlCarousel({
                  loop: true,
                  margin: 10,
                  responsiveClass: true,
                  dots: true,
                  responsive: {
                    0: {
                      items: 2,
                      nav: true
                    },
                    600: {
                      items: 2,
                      nav: false
                    },
                    1000: {
                      items: 8,
                      nav: true,
                      loop: false,
                      margin: 20
                    }
                  }
        });
    },

    _recommendedCarousel() {
        const $slider = this.$('#carousel-2');
        if (!$slider.length) return;

        // Initialize Owl Carousel
        $slider.owlCarousel({
                  loop: true,
                  margin: 10,
                  responsiveClass: true,
                  dots: true,
                  responsive: {
                    0: {
                      items: 2,
                      nav: true
                    },
                    600: {
                      items: 2,
                      nav: false
                    },
                    1000: {
                      items: 8,
                      nav: true,
                      loop: false,
                      margin: 20
                    }
                  }
        });
    },

    _allCarousel() {
        const $slider = this.$('#carousel-3');
        if (!$slider.length) return;

        // Initialize Owl Carousel
        $slider.owlCarousel({
                  loop: true,
                  margin: 10,
                  responsiveClass: true,
                  dots: true,
                  responsive: {
                    0: {
                      items: 2,
                      nav: true
                    },
                    600: {
                      items: 2,
                      nav: false
                    },
                    1000: {
                      items: 8,
                      nav: true,
                      loop: false,
                      margin: 20
                    }
                  }
        });
    },

});
