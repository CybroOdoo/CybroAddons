/** @odoo-module **/

import OrderSummary from 'point_of_sale.OrderSummary';
import Registries from 'point_of_sale.Registries';
import { round_decimals,round_precision } from 'web.utils';

export const PosLoyaltyDeduction = (OrderSummary) =>
    class PosLoyaltyDeduction extends OrderSummary {
        deductLoyaltyPoints() {
            //----to deduct the loyalty points when the order is refunded---
            const order = this.env.pos.get_order();
            let refundedLines = order.orderlines.filter((line) => line.refunded_orderline_id != undefined);
            let pointsReduced = [];
            let newBalance = [];
            let programName= [];
            let valsList = [];
            if(order.couponPointChanges != undefined){
                let rewardPoints =  JSON.parse(localStorage.getItem('pointsCost'))
                for (const pointChange of Object.values(order.getLoyaltyPoints())) {
                    const { couponId,bal, points, program } = pointChange;
                    if(couponId > 0){
                        let loyaltyCard = this.env.pos.couponCache[couponId]
                        let programs = this.env.pos.program_by_id[loyaltyCard.program_id];
                        programName.push(programs.name)
                        let balance = loyaltyCard.balance
                        let res = 0;
                        let ruleId = [];
                        programs.rules.forEach(rule => {
                            ruleId.push(rule.id)
                            let totalQuantity = 0;
                            for (let line of refundedLines) {
                                const refundedQty = line.pos.toRefundLines[line.refunded_orderline_id]?.orderline?.refundedQty - line.get_quantity()
                                switch (rule.reward_point_mode) {
                                    case 'money':
                                        res -= round_precision(rule.reward_point_amount * line.get_price_with_tax(), 0.01);
                                        break;
                                    case 'unit':
                                        res -= rule.reward_point_amount * line.get_quantity();
                                        break;
                                    default:
                                        totalQuantity += line.pos.toRefundLines[line.refunded_orderline_id]?.orderline?.qty || 0;
                                        res += totalQuantity === refundedQty ? rule.reward_point_amount : 0;
                                }
                            }
                        })
                        for(var line of refundedLines){
                        if(line.pos.toRefundLines[line.refunded_orderline_id]?.orderline?.refundedQty === 0 && rewardPoints.length != 0){
                                for(var pointscost of rewardPoints){
                                    if (pointscost[couponId]){
                                        res -= pointscost[couponId]
                                    }
                                }
                            }
                        }
                        let currentBalance = balance - res;
                        valsList.push({lostPoint: res, newPoint: currentBalance.toFixed(2), programName : programs.name, ruleId:ruleId });
                    }
                }
            }
             this.env.pos.lostPoints = valsList;
             return valsList;
    }
    }
Registries.Component.extend(OrderSummary, PosLoyaltyDeduction)
