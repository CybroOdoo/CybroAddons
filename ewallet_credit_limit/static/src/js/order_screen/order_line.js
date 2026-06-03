/** @odoo-module **/
import { Order, Orderline } from "@point_of_sale/app/store/models";
import { formatCurrency } from "@web/core/currency";
import { patch } from "@web/core/utils/patch";

patch(Orderline.prototype, {
    getGiftCardOrEWalletBalance() {
        const coupon = this.pos.couponCache[this.coupon_id];
        const matchedCard = this.pos.loyalty_card.find((loyalty_card) => loyalty_card.id === coupon?.id);
        if (matchedCard && matchedCard.set_limit === true) {
            return formatCurrency(matchedCard.balance_limit_amount || 0, this.currency);
        } else {
            return formatCurrency(coupon?.balance || 0);
        }
    },
});
