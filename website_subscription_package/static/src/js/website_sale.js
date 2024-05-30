/** @odoo-module **/
import { WebsiteSale } from '@website_sale/js/website_sale';
WebsiteSale.include({
    /**
     * Assign the recurrence period to the rootProduct for subscription products.
     *
     * @override
     */
    _updateRootProduct($form, productId) {
        this._super(...arguments);
        Object.assign(this.rootProduct, this._getRecurrencePeriod());
    },
    /**
     * Get selected recurrence period for subscription product from website.
     */
    _getRecurrencePeriod($product) {
        const period = this.$el.find('select[id=recurrence_period]').val();
        if (period) { {
            return {
                period: period,
            };
        }
        }
    },
});
