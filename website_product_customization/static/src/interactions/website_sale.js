/** @odoo-module **/
import { WebsiteSale } from '@website_sale/interactions/website_sale';
import { patch } from '@web/core/utils/patch';
import wSaleUtils from '@website_sale/js/website_sale_utils';
import { CartService } from "@website_sale/js/cart_service";


patch(WebsiteSale.prototype, {
    /**
     * Adds design_image from DOM to the product before adding to cart.
     */
    async onClickAdd(ev) {
        const el = ev.currentTarget;
        const image_element = document.getElementsByClassName("design_image_doc");
        if (image_element.length === 0) {
            return super.onClickAdd(...arguments);
        }
        const design_image = image_element[0].currentSrc || image_element[0].src || '';
        const form = wSaleUtils.getClosestProductForm(el);
        this._updateRootProduct(form);
        this.rootProduct.design_image = design_image;
        window.rootProduct = this.rootProduct;
        image_element[0].remove();
        return super.onClickAdd(...arguments);
    },
});

patch(CartService.prototype, {
    /**
    * Sends design_image along with the cart add request.
    */
    async add(product, options = {}) {
        const designImage =
            product.design_image ||
            (window.rootProduct && window.rootProduct.design_image);
        if (designImage) {
            product.design_image = designImage;
        } else {
            console.warn("⚠️ No design_image found in product or rootProduct");
        }
        // Keep a reference to the original _makeRequest
        const originalMakeRequest = this._makeRequest.bind(this);
        // Monkey-patch _makeRequest to inject design_image
        this._makeRequest = async (data) => {
            if (product.design_image) {
                data.design_image = product.design_image;
            }
            return await originalMakeRequest(data);
        };
        return await super.add(product, options);
    },
});