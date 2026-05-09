/** @odoo-module **/

import { WebsiteSale } from '@website_sale/js/website_sale';
import { rpc } from "@web/core/network/rpc";

WebsiteSale.include({
    /**
     * @override
     */
    _onChangeCombination: async function (ev, $parent, combination) {
        const _super = this._super.bind(this);
        let isHidden = false;
        if (combination.product_id) {
            const result = await rpc('/web/dataset/call_kw/product.product/search_read', {
                model: 'product.product',
                method: 'search_read',
                args: [[['id', '=', parseInt(combination.product_id)]]],
                kwargs: {
                    fields: ['website_hide_variants']
                }
            });
            if (result && result.length > 0 && result[0].website_hide_variants) {
                combination.is_combination_possible = false;
                isHidden = true;
            }
        }

        await _super.apply(this, arguments);

        if (isHidden) {
            const msgEl = $parent.find('.css_not_available_msg')[0] || $parent.closest('.oe_website_sale').find('.css_not_available_msg')[0];
            if (msgEl) {
                msgEl.innerText = "This Product is Out-of-stock.";
            }
        }
    }
});