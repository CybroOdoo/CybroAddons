/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Order } from "@point_of_sale/app/store/models";
import { roundPrecision as round_pr } from "@web/core/utils/numbers";
import {
    formatDate,
    serializeDateTime,
    deserializeDate,
} from "@web/core/l10n/dates";

function _newRandomRewardCode() {
    return (Math.random() + 1).toString(36).substring(3);
}

function _applyRounding(points, precision, mode) {
    const factor = Math.pow(10, precision);
    switch (mode) {
        case 'up':   return Math.ceil(points * factor) / factor;
        case 'down': return Math.floor(points * factor) / factor;
        default:     return Math.round(points * factor) / factor;
    }
}

patch(Order.prototype,{

    async _updatePrograms() {
        await super._updatePrograms(...arguments);
        for (const change of Object.values(this.couponPointChanges)) {
            const program = this.pos.program_by_id[change.program_id];
            if (!program) continue;
            const redemptionReward = this.pos.rewards.find(
                r => r.program_id === program && r.reward_type === 'redemption'
            );
            if (redemptionReward?.rounding_mode) {
                change.points = _applyRounding(
                    change.points,
                    redemptionReward.rounding_precision ?? 0,
                    redemptionReward.rounding_mode
                );
            }
        }
    },

    _getRewardLineValues(args) {
        //---added the new reward type to this function----
        const reward = args["reward"];
        if (reward.reward_type === "discount") {
            return this._getRewardLineValuesDiscount(args);
        } else if (reward.reward_type === "product") {
            return this._getRewardLineValuesProduct(args);
        } else if (reward.reward_type === "redemption"){
            return this._getRewardLineValuesRedemption(args)}
    },

    _applyReward(reward, coupon_id, args) {
        const result = super._applyReward(...arguments);
        
        if (reward.reward_type === 'redemption' && result === true) {
            const salesperson = this.get_order_salesperson?.() ||
                                this.pos.get_cashier?.();
            if (salesperson) {
                for (const line of this._get_reward_lines()) {
                    if (line.coupon_id === coupon_id &&
                        line.reward_id === reward.id &&
                        line.set_line_emp &&
                        !line.get_line_emp?.()) {
                        line.set_line_emp(salesperson);
                    }
                }
            }
        }
        return result;
    },

    _getRewardLineValuesRedemption(args){
        //---reward product for the reward 'redemption'---
        const reward = args["reward"];
        const coupon_id = args["coupon_id"];
        const rewardAppliesTo = reward.discount_applicability;
        let getDiscountable;
        getDiscountable = this._getDiscountableOnOrder.bind(this);
        let { discountable, discountablePerTax } = getDiscountable(reward);
        discountable = Math.min(this.get_total_with_tax(), discountable);
        const discount = reward.pointsToRedeem * reward.redemption_amount
        const discountProduct = reward.discount_line_product_id;
        const rewardCode = _newRandomRewardCode();
        const points = this._getRealCouponPoints(args["coupon_id"])
        const cost = reward.clear_wallet ? points :reward.pointsToRedeem
        return[
        {
            product: discountProduct,
            price: -Math.min(discount),
            quantity: 1,
            reward_id: reward.id,
            is_reward_line: true,
            coupon_id: coupon_id,
            points_cost: cost,
            reward_identifier_code: rewardCode,
            merge: false,
            tax_ids: discountProduct.taxes_id,
        },
        ]
    },

    getLoyaltyPoints() {
        //------change is added to loyalty points---
        // map: couponId -> LoyaltyPoints
        const loyaltyPoints = {};
        for (const pointChange of Object.values(this.couponPointChanges)) {
            const { coupon_id, points, program_id } = pointChange;
            const program = this.pos.program_by_id[program_id];
            if (program.program_type !== "loyalty") {
                continue;
            }
            const loyaltyCard = this.pos.couponCache[coupon_id] || /* or new card */ {
                id: coupon_id,
                balance: 0,
            };
            let [won, spent, total] = [0, 0, 0];

            var balance = loyaltyCard.balance;
            if(this.pos.get_order().convertToLoyalty == undefined){
                won += points - this._getPointsCorrection(program);
            }
            else{
                won += points - this._getPointsCorrection(program);
                if(program_id === this.pos.get_order().programToAdd){
                    won += this.pos.get_order().convertToLoyalty;
                }
            }
            
            for (const line of this._get_reward_lines()) {
                if (!line.reward_id) continue;
                const lineReward = this.pos.reward_by_id[line.reward_id];
                if (lineReward?.reward_type === 'redemption' &&
                    lineReward.program_id.id === program_id) {
                    for (const rule of program.rules) {
                        if (rule.reward_point_mode === 'money') {
                            won -= round_pr(
                                Math.abs(line.get_price_with_tax()) * rule.reward_point_amount,
                                0.01
                            );
                        }
                    }
                }
            }
            if (coupon_id !== 0) {
                for (const line of this._get_reward_lines()) {
                    if (line.coupon_id === coupon_id) {
                        spent += line.points_cost;
                    }
                }
            }
            total = balance + won - spent;
            const name = program.portal_visible ? program.portal_point_name : _t("Points");
            loyaltyPoints[coupon_id] = {
                won: parseFloat(won.toFixed(2)),
                spent: parseFloat(spent.toFixed(2)),
                total: parseFloat(total.toFixed(2)),
                balance: parseFloat(balance.toFixed(2)),
                name,
                program,
            };
        }

        return Object.entries(loyaltyPoints).map(([couponId, points]) => ({
            couponId,
            points,
            program: points.program,
        }));
    },

    get_change(paymentline) {
        //----change is modified when change is added to loyalty points----
        if (!paymentline) {
        if(this.changeConverted == undefined){
            var change =
                this.get_total_paid() - this.get_total_with_tax() - this.get_rounding_applied();
                }
                else{
                var change = 0
                }
        } else {
            change = -this.get_total_with_tax();
            var lines = this.paymentlines;
            for (var i = 0; i < lines.length; i++) {
                change += lines[i].get_amount();
                if (lines[i] === paymentline) {
                    break;
                }
            }
        }
        return round_pr(Math.max(0, change), this.pos.currency.rounding);
    },

    export_as_JSON() {
        //when change is converted the amount returned is changed
        var orderLines, paymentLines;
        orderLines = [];
        this.orderlines.forEach((item) => {
            return orderLines.push([0, 0, item.export_as_JSON()]);
        });
        paymentLines = [];
        this.paymentlines.forEach((item) => {
            const itemAsJson = item.export_as_JSON();
            if (itemAsJson) {
                return paymentLines.push([0, 0, itemAsJson]);
            }
        });
        var json = {
            name: this.get_name(),
            amount_paid: this.get_total_paid() - this.get_change(),
            amount_total: this.get_total_with_tax(),
            amount_tax: this.get_total_tax(),
            amount_return: this.get_total_paid() - this.get_total_with_tax() - this.get_rounding_applied(),
            lines: orderLines,
            statement_ids: paymentLines,
            pos_session_id: this.pos_session_id,
            pricelist_id: this.pricelist ? this.pricelist.id : false,
            partner_id: this.get_partner() ? this.get_partner().id : false,
            user_id: this.pos.user.id,
            uid: this.uid,
            sequence_number: this.sequence_number,
            date_order: serializeDateTime(this.date_order),
            fiscal_position_id: this.fiscal_position ? this.fiscal_position.id : false,
            server_id: this.server_id ? this.server_id : false,
            to_invoice: this.to_invoice ? this.to_invoice : false,
            shipping_date: this.shippingDate ? this.shippingDate : false,
            is_tipped: this.is_tipped || false,
            tip_amount: this.tip_amount || 0,
            access_token: this.access_token || "",
            last_order_preparation_change: JSON.stringify(this.lastOrderPrepaChange),
            ticket_code: this.ticketCode || "",
        };
        if (!this.is_paid && this.user_id) {
            json.user_id = this.user_id;
        }
        return json;
    }
})