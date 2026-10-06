/** @odoo-module **/

import { renderToElement } from "@web/core/utils/render";
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
import wSaleUtils from "@website_sale/js/website_sale_utils";

function chunk(array, size) {
    const chunks = [];
    for (let i = 0; i < array.length; i += size) {
        chunks.push(array.slice(i, i + size));
    }
    return chunks;
}

publicWidget.registry.TrendingCourses = publicWidget.Widget.extend({
    selector: '.s_top_trending_courses',
    events: {
        'click .js_add_to_cart_btn': '_onAddToCart',
    },

    async willStart() {
        const result = await jsonrpc('/latest_products', {});
        if (result && result.products && result.products.length > 0) {
            const chunks = chunk(result.products, 3);
            chunks[0].is_active = true;
            const uniq = Date.now();
            const content = renderToElement(
                'theme_educational.top_trending_courses_snippet',
                {
                    product_chunks: chunks,
                    uniq: uniq,
                }
            );
            this.$target.empty().append(content);
        }
    },

    /**
     * Handle click on Add to Cart button in trending courses snippet cards.
     *
     * @param {Event} ev
     */
    async _onAddToCart(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        const $btn = $(ev.currentTarget);
        const productId = parseInt($btn.attr('data-product-id') || $btn.data('product-id'), 10);
        if (!productId) {
            // Fallback: navigate to product page if no variant ID
            const productUrl = $btn.closest('.custom-course-card').find('a[href]').attr('href');
            if (productUrl) {
                window.location.href = productUrl;
            }
            return;
        }

        $btn.addClass('disabled').prop('disabled', true);
        const originalHtml = $btn.html();
        $btn.html('<i class="fa fa-spinner fa-spin me-1"/> Adding...');

        try {
            const data = await jsonrpc("/shop/cart/update_json", {
                product_id: productId,
                add_qty: 1,
                display: false,
                force_create: true,
            });

            if (data && !data.error) {
                // 1. Immediately update cart quantity badge in navbar
                if (data.cart_quantity !== undefined) {
                    $('.my_cart_quantity').text(data.cart_quantity).removeClass('d-none');
                    $('.o_wsale_my_cart').removeClass('d-none');
                }

                // 2. Safely call updateCartNavBar to refresh session and cart widgets
                try {
                    if (typeof wSaleUtils !== 'undefined' && wSaleUtils.updateCartNavBar) {
                        wSaleUtils.updateCartNavBar(data);
                    }
                } catch (navErr) {
                    console.warn("Could not execute updateCartNavBar:", navErr);
                }

                // 3. Trigger flying product image animation to the cart
                try {
                    if (typeof wSaleUtils !== 'undefined' && wSaleUtils.animateClone) {
                        const $cart = $('header .o_wsale_my_cart, header .my_cart_quantity').first();
                        wSaleUtils.animateClone($cart, $btn.closest('.custom-course-card'), 25, 30);
                    }
                } catch (animErr) {
                    // Ignore animation errors
                }

                // 4. Safely display cart notification popup
                try {
                    if (typeof wSaleUtils !== 'undefined' && wSaleUtils.showCartNotification && data.notification_info && typeof this.call === 'function') {
                        wSaleUtils.showCartNotification(this.call.bind(this), data.notification_info);
                    }
                } catch (notifErr) {
                    console.warn("Could not display cart notification:", notifErr);
                }

                // 5. Button success feedback state
                $btn.html('<i class="fa fa-check me-1"/> Added');
                setTimeout(() => {
                    $btn.removeClass('disabled').prop('disabled', false).html(originalHtml);
                }, 1500);
            } else {
                const productUrl = $btn.closest('.custom-course-card').find('a[href]').attr('href');
                if (productUrl) {
                    window.location.href = productUrl;
                } else {
                    $btn.removeClass('disabled').prop('disabled', false).html(originalHtml);
                }
            }
        } catch (error) {
            console.error("Failed to add product to cart:", error);
            const productUrl = $btn.closest('.custom-course-card').find('a[href]').attr('href');
            if (productUrl) {
                window.location.href = productUrl;
            } else {
                $btn.removeClass('disabled').prop('disabled', false).html(originalHtml);
            }
        }
    },
});

publicWidget.registry.EducationalFaq = publicWidget.Widget.extend({
    selector: '.section-faq',
    events: {
        'click .card-header a, click [data-toggle="collapse"], click [data-bs-toggle="collapse"]': '_onFaqToggle',
    },

    /**
     * Handle accordion toggle on FAQ items, supporting both BS4 and BS5 attributes
     * and ensuring smooth collapse transitions across all pages.
     *
     * @param {Event} ev
     */
    _onFaqToggle(ev) {
        ev.preventDefault();
        const $link = $(ev.currentTarget);
        const targetSelector = $link.attr('data-bs-target') || $link.attr('data-target') || $link.attr('href');
        if (!targetSelector || targetSelector === '#') {
            return;
        }

        const targetEl = this.el.querySelector(targetSelector) || document.querySelector(targetSelector);
        if (!targetEl) {
            return;
        }

        if (window.bootstrap && window.bootstrap.Collapse) {
            const parentSelector = targetEl.getAttribute('data-bs-parent') || targetEl.getAttribute('data-parent');
            const collapseInstance = window.bootstrap.Collapse.getOrCreateInstance(targetEl, {
                parent: parentSelector || false,
                toggle: false,
            });
            collapseInstance.toggle();
        } else if ($.fn.collapse) {
            $(targetEl).collapse('toggle');
        }
    },
});

