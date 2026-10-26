/** @odoo-module **/
import { AddToCart } from '@website_sale/interactions/add_to_cart';
import { patch } from '@web/core/utils/patch';

/**
 * Patch AddToCart to include the design_image in the product data
 * sent when adding a product to the cart.
 */
patch(AddToCart.prototype, {
    /**
     * Override to inject design_image from the DOM into the cart payload.
     * _getOptionalParams is the intended hook for adding extra data.
     *
     * @param {HTMLElement} el - The element containing the product.
     * @returns {Object} - Additional params including design_image if present.
     */
    _getOptionalParams(el) {
        const result = super._getOptionalParams(el);
        const imageElements = document.getElementsByClassName("design_image_doc");
        if (imageElements.length > 0) {
            const design_image = imageElements[0].currentSrc || imageElements[0].src || '';
            if (design_image) {
                result.design_image = design_image;
                // Clean up the temporary image element after capturing
                imageElements[0].remove();
            }
        }
        return result;
    },
});