/** @odoo-module **/
import { Order } from "@point_of_sale/app/store/models";
import { roundPrecision } from "@web/core/utils/numbers";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {

    deductLoyaltyPoints(product) {
    // -----------To show the deducted loyalty points on pos screen-----------
        let refundedLines = this.get_orderlines().filter((line) => line.refunded_orderline_id);
        // Lines with negative qty and no linked order = unlinked refund
        let unlinkedRefundLines = refundedLines.length === 0
            ? this.get_orderlines().filter((line) => !line.is_reward_line && line.get_quantity() < 0)
            : [];
        let valsList = [];
        if (this.couponPointChanges) {
            if (refundedLines.length > 0) {
                // Linked refund — existing logic
                let rewardPoints = JSON.parse(localStorage.getItem('pointsCost'));
                this.getLoyaltyPoints().forEach((record) => {
                    let { couponId, points, program } = record;
                    if (couponId > 0) {
                        let loyaltyCard = this.pos.couponCache[couponId];
                        let programs = this.pos.program_by_id[loyaltyCard.program_id];
                        let balance = loyaltyCard.balance;
                        let res = 0;
                        let ruleId = [];
                        programs.rules.forEach(rule => {
                            ruleId.push(rule.id);
                            let totalQuantity = 0;
                            for (let line of refundedLines) {
                                const refundedQty = line.pos.toRefundLines[line.refunded_orderline_id]?.orderline?.refundedQty - line.get_quantity();
                                switch (rule.reward_point_mode) {
                                    case 'money':
                                        res -= roundPrecision(rule.reward_point_amount * line.get_price_with_tax(), 0.01);
                                        break;
                                    case 'unit':
                                        res -= rule.reward_point_amount * line.get_quantity();
                                        break;
                                    default:
                                        totalQuantity += line.pos.toRefundLines[line.refunded_orderline_id]?.orderline?.qty || 0;
                                        res += totalQuantity === refundedQty ? rule.reward_point_amount : 0;
                                }
                            }
                        });
                        for (var line of refundedLines) {
                            if (line.pos.toRefundLines[line.refunded_orderline_id]?.orderline?.refundedQty === 0 && rewardPoints.length != 0) {
                                for (var pointscost of rewardPoints) {
                                    if (pointscost[couponId]) {
                                        res -= pointscost[couponId];
                                    }
                                }
                            }
                        }
                        let currentBalance = balance - res;
                        valsList.push({ lostPoint: res, newPoint: currentBalance.toFixed(2), programName: programs.name, ruleId: ruleId });
                    }
                });
            } else if (unlinkedRefundLines.length > 0) {
                // Unlinked refund — negative qty lines entered manually
                this.getLoyaltyPoints().forEach((record) => {
                    let { couponId, points, program } = record;
                    if (couponId > 0) {
                        let loyaltyCard = this.pos.couponCache[couponId];
                        let programs = this.pos.program_by_id[loyaltyCard.program_id];
                        let balance = loyaltyCard.balance;
                        let res = 0;
                        let ruleId = [];
                        programs.rules.forEach(rule => {
                            ruleId.push(rule.id);
                            let orderModeProcessed = false;
                            for (let line of unlinkedRefundLines) {
                                switch (rule.reward_point_mode) {
                                    case 'money':
                                        res -= roundPrecision(rule.reward_point_amount * line.get_price_with_tax(), 0.01);
                                        break;
                                    case 'unit':
                                        res -= rule.reward_point_amount * line.get_quantity();
                                        break;
                                    case 'order':
                                        if (!orderModeProcessed) {
                                            res += rule.reward_point_amount;
                                            orderModeProcessed = true;
                                        }
                                        break;
                                }
                            }
                        });
                        let currentBalance = balance - res;
                        valsList.push({ lostPoint: res, newPoint: currentBalance.toFixed(2), programName: programs.name, ruleId: ruleId });
                    }
                });
            }
        }
        this.pos.lostPoints = valsList;
        return valsList;
    },
})