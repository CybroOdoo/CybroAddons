/** @odoo-module **/
/**
 * Theme Cordage – AJAX Add-to-Cart for Homepage Product Cards
 *
 * The Shop page uses Odoo's built-in `data-add2cart-redirect="1"` mechanism
 * (set in theme_cordage_cart_no_redirect template) which already handles
 * AJAX cart updates for the .oe_website_sale widget.
 *
 * This widget handles the HOMEPAGE product cards only, which render
 * outside the .oe_website_sale scope and use a raw <form> POST.
 * We intercept that form submission and convert it to an AJAX call
 * so the page is not redirected.
 */

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

// ---------------------------------------------------------------------------
// Helper: update the cart badge counter in the navbar
// ---------------------------------------------------------------------------

/**
 * Updates all cart quantity badge elements in the navbar with the latest
 * cart item count and briefly triggers a zoom animation for visual feedback.
 * Also persists the quantity in sessionStorage so it survives soft navigations.
 *
 * @param {number} quantity - The total number of items currently in the cart.
 *   Pass 0 or falsy to clear the badge text.
 * @returns {void}
 */
function updateCartBadge(quantity) {
    const badges = document.querySelectorAll(".my_cart_quantity");
    for (const badge of badges) {
        const li = badge.closest("li");
        if (li) li.classList.remove("d-none");
        badge.classList.remove("d-none");
        badge.textContent = quantity || "";
        badge.classList.add("o_mycart_zoom_animation");
        setTimeout(() => badge.classList.remove("o_mycart_zoom_animation"), 600);
    }
    try { sessionStorage.setItem("website_sale_cart_quantity", quantity); } catch (_) { /* noop */ }
}

// ---------------------------------------------------------------------------
// Helper: show a brief success/error toast
// ---------------------------------------------------------------------------

/**
 * Displays a transient toast notification at the bottom of the page.
 * Any existing toast is removed before showing the new one.
 * The toast auto-dismisses after 2.5 seconds with a CSS fade-out transition.
 *
 * @param {string} message - The human-readable message to display inside the toast.
 * @param {"success"|"error"} [type="success"] - Visual variant of the toast.
 *   - `"success"` renders a green check-circle icon.
 *   - `"error"` renders a red exclamation-circle icon.
 * @returns {void}
 */
function showToast(message, type = "success") {
    document.querySelector(".tc-cart-toast")?.remove();

    const toast = document.createElement("div");
    toast.className = `tc-cart-toast tc-cart-toast--${type}`;
    toast.innerHTML = `
        <span class="tc-cart-toast__icon fa ${type === "success" ? "fa-check-circle" : "fa-exclamation-circle"}"></span>
        <span class="tc-cart-toast__msg">${message}</span>
    `;
    document.body.appendChild(toast);

    requestAnimationFrame(() => {
        requestAnimationFrame(() => toast.classList.add("tc-cart-toast--visible"));
    });

    setTimeout(() => {
        toast.classList.remove("tc-cart-toast--visible");
        setTimeout(() => toast.remove(), 400);
    }, 2500);
}

// ---------------------------------------------------------------------------
// Helper: extract form data as a plain object
// ---------------------------------------------------------------------------

/**
 * Converts a standard HTML `<form>` element's serialised fields into a plain
 * key-value object using the `FormData` API.
 *
 * Note: Only the first value is kept for each key (multi-value fields such as
 * checkboxes with the same name are not aggregated into arrays).
 *
 * @param {HTMLFormElement} form - The form element whose data should be extracted.
 * @returns {Object.<string, string>} A plain object mapping each field name to
 *   its string value as returned by `FormData`.
 */
function formDataToObject(form) {
    const fd = new FormData(form);
    const obj = {};
    for (const [key, value] of fd.entries()) {
        obj[key] = value;
    }
    return obj;
}

// ---------------------------------------------------------------------------
// Widget – handles homepage product card forms only
// ---------------------------------------------------------------------------

publicWidget.registry.ThemeCordageCart = publicWidget.Widget.extend(/**
 * @lends publicWidget.registry.ThemeCordageCart.prototype
 */ {
    selector: "#wrapwrap",

    events: {
        // Homepage product-card form submit (button[type=submit] inside the form)
        "submit .theme-cordage-product-card": "_onCardFormSubmit",
    },

    /**
     * Handles the `submit` event fired by a homepage product-card form
     * (`.theme-cordage-product-card`).
     *
     * Prevents the default browser POST redirect and instead sends an
     * asynchronous JSON-RPC request to `/shop/cart/update_json`.
     * On success the navbar cart badge is refreshed and a success toast is shown.
     * On failure an error toast is displayed and the original button label is
     * restored so the user can retry.
     *
     * @param {Event} ev - The DOM `submit` event originating from the product
     *   card form. `ev.currentTarget` is the `<form>` element.
     * @returns {Promise<void>} Resolves when the cart update request has
     *   completed (successfully or with an error).
     */
    async _onCardFormSubmit(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        const form = ev.currentTarget;
        const btn = form.querySelector("[type='submit']");
        if (!btn || btn.disabled) return;

        const formObj = formDataToObject(form);
        const productId = parseInt(formObj.product_id, 10);
        const qty = parseInt(formObj.add_qty, 10) || 1;

        if (!productId) {
            showToast("Product not available.", "error");
            return;
        }

        // Visual feedback on the button
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="fa fa-spinner fa-spin"></span>';

        try {
            const data = await jsonrpc("/shop/cart/update_json", {
                product_id: productId,
                add_qty: qty,
                display: false,
                force_create: true,
            });

            if (data && data.cart_quantity != null) {
                updateCartBadge(data.cart_quantity);
            }
            showToast("Added to cart!");
        } catch (err) {
            console.error("[Cordage] Add to cart error:", err);
            showToast("Could not add to cart. Please try again.", "error");
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    },
});
