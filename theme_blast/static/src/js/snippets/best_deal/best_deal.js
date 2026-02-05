/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";
import publicWidget from "@web/legacy/js/public/public_widget";
import wSaleUtils from "@website_sale/js/website_sale_utils";
import { Component } from "@odoo/owl";

// Add safe check for jQuery, though it should be available in publicWidget context
const $ = window.jQuery;

publicWidget.registry.BestDeal = publicWidget.Widget.extend({
    selector: '.best_deal',
    events: {
        'click .btn-buy-now': '_onClickBuyNow',
    },

    /**
     * @override
     * Initializes the widget, fetches product data and starts the countdown timer.
     */
    start: async function () {
        const self = this;

        // --- Product Display ---
        const products = await rpc('/get_product', {});
        if (products) {
            // $target is the jQuery object for the element matched by the selector ('.best_deal')
            self.$target.html(products);
        }

        // --- Countdown Timer ---
        const countdown = await rpc('/get_countdown', {});
        if (countdown) {
            const end_date = new Date(countdown).getTime();

            // NOTE: Consider using this.interval = setInterval(...) and clearing it in destroy()
            // for proper widget lifecycle management if the widget can be removed from the DOM.
            setInterval(function () {
                const start_date = new Date().getTime();
                // Calculate seconds left and ensure time doesn't go negative for display
                let seconds_left = (end_date - start_date) / 1000;

                // Only proceed if the countdown is still positive
                if (seconds_left > 0) {
                    const days = Math.floor(seconds_left / 86400);
                    seconds_left %= 86400;
                    const hours = Math.floor(seconds_left / 3600);
                    seconds_left %= 3600;
                    const minutes = Math.floor(seconds_left / 60);
                    const seconds = Math.floor(seconds_left % 60);

                    $("#countdown").html(
                        `<span class="days">${days} <label>Days</label></span>
                         <span class="hours">${hours} <label>Hours</label></span>
                         <span class="minutes">${minutes} <label>Minutes</label></span>
                         <span class="seconds">${seconds} <label>Seconds</label></span>`
                    );
                } else {
                    // Display 00:00:00:00 when the countdown is over
                    $("#countdown").html(
                        `<span class="days">0 <label>Days</label></span>
                         <span class="hours">0 <label>Hours</label></span>
                         <span class="minutes">0 <label>Minutes</label></span>
                         <span class="seconds">0 <label>Seconds</label></span>`
                    );
                }
            }, 1000);
        }
    },

    /**
     * Handles the click on the 'Buy now' button, adding the product to the cart.
     * @private
     * @param {Event} ev - The click event.
     */
    _onClickBuyNow: function (ev) {
        ev.preventDefault(); // Prevent default button action if any

        const $target = $(ev.currentTarget);
        const productId = $target.data('product-id');
        const lineId = parseInt(ev.currentTarget.dataset.lineId, 10);
        const self = this;

        // Perform RPC to add the product to the cart
        rpc('/shop/cart/update', {
            display: false, // Prevents redirection to cart (usually)
            product_id: productId,
            quantity: 1,
            line_id: lineId || null, // Ensure line_id is null if not present
        }).then((result) => {
            // --- Cart UI Update Logic (Fix for the original error) ---

            // Define the most critical elements required for updateCartNavBar
            // The original error was caused by a missing 'li.o_wsale_my_cart' inside updateCartNavBar.
            // We now explicitly check for the element required by updateCartNavBar or any cart element.
            const requiredCartElement = document.querySelector('li.o_wsale_my_cart');

            // Check for the required element or general cart elements before calling the utility.
            if (requiredCartElement || document.querySelector('.o_wsale_my_cart_icon, .o_wsale_topbar, .o_wsale_cart_navbar')) {
                // Call the utility function to update the cart icon and price displays
                wSaleUtils.updateCartNavBar(result);
            }

            // --- Notifications ---
            if (result.notification_info) {
                if (result.notification_info.warning) {
                    wSaleUtils.showWarning(result.notification_info.warning);
                }
                // Show the standard cart notification (e.g., product added message)
                wSaleUtils.showCartNotification(self.call.bind(self), result.notification_info);
            }

            // --- Bus Trigger (for updating price/amount displays in other Owl components) ---
            Component.env.bus.trigger('cart_amount_changed', [result.amount, result.minor_amount]);
        });
    },
});