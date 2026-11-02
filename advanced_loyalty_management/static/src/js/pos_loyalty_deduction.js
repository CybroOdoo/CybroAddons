/** @odoo-module **/
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

function _newRandomRewardCode() {
    return (Math.random() + 1).toString(36).substring(3);
}

patch(PosOrder.prototype, {
    _getRewardLineValues(args) {
        if (args["reward"]?.reward_type === "redemption") {
            return this._getRewardLineValuesRedemption(args);
        }
        return super._getRewardLineValues(...arguments);
    },

    _getRewardLineValuesRedemption(args) {
        const reward = args["reward"];
        const coupon_id = args["coupon_id"];

        let discountable = this
            .getOrderlines()
            .filter(
                (line) =>
                    !line.is_reward_line &&
                    !line.combo_parent_id &&
                    !line.isTipLine() &&
                    line.getQuantity() > 0 &&
                    line.linePriceTaxIncluded > 0 &&
                    !line.isServiceFeeLine()
            )
            .reduce(
                (total, line) =>
                    total + this.getLineDiscountablePrice(line.uuid),
                0
            );

        discountable = Math.min(this.priceIncl, discountable);

        const pointsToRedeem = reward.pointsToRedeem || 0;

        let discount =
            pointsToRedeem * (reward.redemption_amount || 0);

        if (reward.max_redemption_amount > 0) {
            if (reward.max_redemption_type === "amount") {
                discount = Math.min(
                    discount,
                    reward.max_redemption_amount
                );
            } else if (reward.max_redemption_type === "percent") {
                const maxAmount =
                    (this.priceIncl * reward.max_redemption_amount) / 100;
                discount = Math.min(discount, maxAmount);
            } else if (reward.max_redemption_type === "points") {
                const maxAmount =
                    reward.max_redemption_amount * (reward.redemption_amount || 0);
                discount = Math.min(discount, maxAmount);
            }
        }

        discount = Math.min(discount, discountable);

        const discountProduct =
            reward.discount_line_product_id ||
            reward.program_id.reward_product_id;

        const rewardCode = _newRandomRewardCode();

        const program = reward.program_id;
        const card =
            program &&
            this.models["loyalty.card"].find(
                (card) =>
                    card.program_id?.id === program.id &&
                    this.applied_codes.includes(card.code)
            );

        const points = card?.points || 0;
        if (pointsToRedeem > points) {
            return [];
        }
        const cost = reward.clear_wallet ? points : pointsToRedeem;

        return [
            {
                product_id: discountProduct,
                price_unit: -discount,
                qty: 1,
                reward_id: reward,
                is_reward_line: true,
                _reward_product_id: discountProduct,
                points_cost: cost,
                reward_identifier_code: rewardCode,
                tax_ids: discountProduct?.taxes_id
                    ? discountProduct.taxes_id.map((tax) => ["link", tax])
                    : [],
            },
        ];
    },

    get change() {
        const raw = super.change;
        const converted = this.convertedChange || 0;
        if (!converted) {
            return raw;
        }
        const left = Math.max(0, Math.abs(raw || 0) - converted);
        if (left < 0.005) {
            return 0;
        }
        return raw < 0 ? -left : left;
    },

    setOrderPrices() {
        const converted = this.convertedChange;
        this.convertedChange = 0;
        try {
            return super.setOrderPrices(...arguments);
        } finally {
            this.convertedChange = converted;
        }
    },
});
