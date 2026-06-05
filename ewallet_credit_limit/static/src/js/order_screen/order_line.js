/** @odoo-module **/
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { formatCurrency } from "@point_of_sale/app/models/utils/currency";
import { patch } from "@web/core/utils/patch";

patch(PosOrderline.prototype, {
    getGiftCardOrEWalletBalance() {
        const coupon = this.coupon_id;
        if (coupon && coupon.set_limit === true) {
            return formatCurrency(coupon.balance_limit_amount || 0, this.currency);
        } else {
            return formatCurrency(coupon?.points || 0, this.currency);
        }
    },
});
