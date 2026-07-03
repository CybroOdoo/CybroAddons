/** @odoo-module **/
import { OrderSummary } from "@point_of_sale/app/screens/product_screen/order_summary/order_summary";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { roundPrecision } from "@web/core/utils/numbers";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";


function _newRandomRewardCode() {
    return (Math.random() + 1).toString(36).substring(3);
}

patch(PosOrder.prototype, {

    deductLoyaltyPoints() {
    // -----------To show the deducted loyalty points on pos screen-----------
        let refundedLines = this.get_orderlines().filter((line) => line.refunded_orderline_id);
        let pointsReduced = [];
        let newBalance = [];
        let programName= [];
        let valsList = [];
        if (this.uiState.couponPointChanges) {
         let refundedLines = this.get_orderlines().filter((line) => line.refunded_orderline_id);
         let refundIds = refundedLines.map(line => line.refunded_orderline_id);
         let rewardPoints =  JSON.parse(localStorage.getItem('pointsCost'))
            this.getLoyaltyPoints().forEach((record) => {
                let { couponId, points, program } = record;
                if (couponId > 0) {
                    let loyaltyCard = this.models["loyalty.card"].get(couponId)
                    const programs = this.models["loyalty.program"].get(program.id);
                    let balance = loyaltyCard.points;
                    let res = 0;
                    let ruleId = [];
                    const allLineToRefundUuids = this.models["pos.order"].reduce((acc, order) => {
                            Object.assign(acc, order.uiState.lineToRefund);
                            return acc;
                        }, {});
                    programs.rule_ids.forEach(rule => {
                        ruleId.push(rule.id);
                        let totalQuantity = 0;
                        for (let line of refundedLines) {
                            const refundedQty = allLineToRefundUuids[line.refunded_orderline_id.uuid]?.orderline?.refunded_qty - line.get_quantity()
                            switch (rule.reward_point_mode) {
                                case 'money':
                                    res -= roundPrecision(rule.reward_point_amount * line.get_price_with_tax(), 0.01);
                                    break;
                                case 'unit':
                                    res -= rule.reward_point_amount * line.get_quantity();
                                    break;
                                default:
                                    totalQuantity += allLineToRefundUuids[line.refunded_orderline_id.uuid]?.orderline?.qty || 0;
                                    res += totalQuantity === refundedQty ? rule.reward_point_amount : 0;
                            }
                        }
                    })
                    for(var line of refundedLines){
                        if(allLineToRefundUuids[line.refunded_orderline_id.uuid]?.orderline?.refunded_qty === 0 && rewardPoints.length != 0){
                                for(var pointscost of rewardPoints){
                                    if (pointscost[couponId]){
                                        res -= pointscost[couponId]
                                    }
                                }
                            }
                        }
                    let currentBalance = balance - res;
                    valsList.push({lostPoint: res, newPoint: currentBalance.toFixed(2), programName : programs.name, ruleId:ruleId })
                }
            })
        }
        return valsList;
    },

    export_for_printing() {
    //--------To show the deducted loyalty points details in the order receipt
        const result = super.export_for_printing(...arguments);
        result.pointsDeducted = this.deductLoyaltyPoints()
        return result;
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

    _getRewardLineValuesRedemption(args){
        //---Reward product for the reward 'redemption'---
        const reward = args["reward"];
        const product =
            reward.program_id.reward_product_id
        const coupon_id = args["coupon_id"];
        const rewardAppliesTo = reward.discount_applicability;
        let getDiscountable;
        getDiscountable = this._getDiscountableOnOrder.bind(this);
        let { discountable, discountablePerTax } = getDiscountable(reward);
        discountable = Math.min(this.get_total_with_tax(), discountable);
        const discount = reward.pointsToRedeem * reward.redemption_amount
        const discountProduct = reward.discount_line_product_id;
        const rewardCode = _newRandomRewardCode();
        const points = this._getRealCouponPoints(args["coupon_id"]);
        const cost = reward.clear_wallet ? points :reward.pointsToRedeem
        return[
        {
            product_id: discountProduct,
            price_unit: -Math.min(discount),
            qty: 1,
            reward_id: reward,
            is_reward_line: true,
            _reward_product_id: discountProduct,
            coupon_id:  args["coupon_id"],
            points_cost: cost,
            reward_identifier_code: rewardCode,
            tax_ids: discountProduct.taxes_id,
        },
        ];
    },

    get_change(paymentline) {
        //----Change is modified when change is added to loyalty points----
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
        return roundPrecision(Math.max(0, change), this.currency.rounding);
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
    },
})