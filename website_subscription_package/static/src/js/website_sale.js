/** @odoo-module **/
import { WebsiteSale } from 'website_sale.website_sale';
WebsiteSale.include({
    /**
     * Assign the recurrence period to the rootProduct for subscription products.
     *
     * @override
     */
    _submitForm: function () {
        const params = this.rootProduct;
        const $product = $('#product_detail');
        const recurrence = $('#recurrence_period')[0];
        let recurrence_id = 0;
        const productTrackingInfo = $product.data('product-tracking-info');
        if (productTrackingInfo) {
            productTrackingInfo.quantity = params.quantity;
            $product.trigger('add_to_cart_event', [productTrackingInfo]);
        }
        for (let item of recurrence) {
            if (item.selected === true) {
                recurrence_id = item.value;
            }
        }
        params.add_qty = params.quantity;
        params.product_custom_attribute_values = JSON.stringify(params.product_custom_attribute_values);
        params.no_variant_attribute_values = JSON.stringify(params.no_variant_attribute_values);
        params['period'] = recurrence_id;
    return this.addToCart(params);
},
});
