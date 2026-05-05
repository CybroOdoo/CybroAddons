/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.WebsiteMultiCart = publicWidget.Widget.extend({
    selector: ".oe_website_sale",
    events: {
        "click .confirm_check": "_onClickCartQuantity",
    },

    /**
     * Add selected products to cart when button is clicked
     * @param {Event} ev - Click event
     */
    async _onClickCartQuantity(ev) {
        ev.preventDefault();

        let self = this;
        let selectedProducts = [];
        let checkBoxes = document.querySelectorAll(".mycheckbox");

        checkBoxes.forEach((item) => {
            if (item.checked) {
                selectedProducts.push(item.value);
            }
        });

        if (selectedProducts.length === 0) {
            this._showNotification("Please select at least one product", "warning");
            return;
        }

        const button = ev.currentTarget;
        const originalContent = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Adding...';

        try {
            const response = await rpc("/shop/cart/add_multi_product", {
                product_ids: selectedProducts,
            });

            if (response && response.total_qty !== undefined) {
                let totalQty = response.total_qty;

                sessionStorage.setItem("website_sale_cart_quantity", totalQty);

                let cartQuantityElement = document.querySelector(".my_cart_quantity");
                if (cartQuantityElement) {
                    cartQuantityElement.textContent = totalQty;
                }

                checkBoxes.forEach((item) => {
                    item.checked = false;
                });

                let message = `${response.added_qty} product(s) added to cart`;
                if (response.failed_products && response.failed_products.length > 0) {
                    message += `. ${response.failed_products.length} product(s) could not be added.`;
                }
                this._showNotification(message, "success");

                setTimeout(() => {
                    window.location.href = "/shop/cart";
                }, 1500);

            } else {
                this._showNotification("Error adding products to cart", "danger");
                button.disabled = false;
                button.innerHTML = originalContent;
            }
        } catch (error) {
            this._showNotification("Error adding products to cart: " + error.message, "danger");
            button.disabled = false;
            button.innerHTML = originalContent;
        }
    },

    /**
     * Show notification to user
     * @param {string} message - Message to display
     * @param {string} type - Bootstrap alert type (success, warning, danger, info)
     */
    _showNotification(message, type) {
        const existingNotifications = document.querySelectorAll('.multi-cart-notification');
        existingNotifications.forEach(notif => notif.remove());

        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show multi-cart-notification`;
        notification.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 9999; min-width: 300px; max-width: 500px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            if (notification && notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    },
});

export default publicWidget.registry.WebsiteMultiCart;