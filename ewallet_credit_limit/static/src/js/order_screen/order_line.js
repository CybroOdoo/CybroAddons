/** @odoo-module **/
import Orderline from 'point_of_sale.Orderline';
import Registries from 'point_of_sale.Registries';

export const PosLoyaltyOrderline = (Orderline) =>
    class extends Orderline {
        _getGiftCardOrEWalletBalance() {
            const coupon = this.env.pos.couponCache[this.props.line.coupon_id];
            const MatchedCard = this.env.pos.loyalty_card.find((loyalty_card) => loyalty_card.id == coupon?.id)
            if (coupon && MatchedCard?.set_limit === true) {
                return this.env.pos.format_currency(Math.min(MatchedCard.balance_limit_amount, coupon.balance));
            } else if (coupon) {
                return this.env.pos.format_currency(coupon.balance);
            }
            return this.env.pos.format_currency(0);
        }
    };

Registries.Component.extend(Orderline, PosLoyaltyOrderline);
