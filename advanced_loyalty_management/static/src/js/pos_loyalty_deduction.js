/** @odoo-module **/
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { patch } from "@web/core/utils/patch";
import { omit } from "@web/core/utils/objects";


function _newRandomRewardCode() {
    return (Math.random() + 1).toString(36).substring(3);
}

patch(PosOrder.prototype, {

    _calculateOrderDeductions(order, loyaltyCard) {
        if (!order || !loyaltyCard) {
            return 0;
        }
        const allLines = order.getOrderlines();
        const refundedProductLines = allLines.filter((line) => line.refunded_orderline_id && !line.refunded_orderline_id.is_reward_line);
        const refundedRewardLines = allLines.filter((line) => line.refunded_orderline_id && line.refunded_orderline_id.is_reward_line);

        let orderPointsLost = 0;
        const program = loyaltyCard.program_id;
        if (!program) {
            return 0;
        }
        const rules = program.rule_ids || [];

        // 1. Calculate points lost for refunded products
        for (const rule of rules) {
            // Filter valid lines for this rule
            const validRefundLines = refundedProductLines.filter((line) => {
                const productId = line.product_id?.id ?? line.product_id;
                return rule.any_product || (rule.validProductIds instanceof Set && rule.validProductIds.has(productId));
            });

            if (validRefundLines.length === 0 && rule.reward_point_mode !== "order") {
                continue;
            }

            if (rule.reward_point_mode === "money") {
                for (const line of validRefundLines) {
                    orderPointsLost += (rule.reward_point_amount || 0) * Math.abs(line.prices?.total_included || 0);
                }
            } else if (rule.reward_point_mode === "unit") {
                for (const line of validRefundLines) {
                    orderPointsLost += (rule.reward_point_amount || 0) * Math.abs(line.getQuantity ? line.getQuantity() : (line.qty || 0));
                }
            } else if (rule.reward_point_mode === "order") {
                // Points per order: only deduct if the ENTIRE order (all lines) is being returned
                const originalOrder = order.refunded_order_id;

                if (!originalOrder) {
                    continue;
                }

                // Calculate cumulative quantities
                let totalOriginalQty = 0;
                let totalCumulativeRefundQty = 0;
                for (const l of originalOrder.lines) {
                    if (!l.is_reward_line) {
                        totalOriginalQty += Math.abs(l.qty || 0);
                        totalCumulativeRefundQty += Math.abs(l.refundedQty || 0);
                    }
                }

                let totalCurrentOrderRefundQty = 0;
                for (const l of order.lines) {
                    if (!l.is_reward_line && l.refunded_orderline_id) {
                        totalCurrentOrderRefundQty += Math.abs(l.qty || 0);
                    }
                }

                const previousRefundQty = totalCumulativeRefundQty - totalCurrentOrderRefundQty;
                const EPSILON = 0.0001;
                if (totalOriginalQty > EPSILON && totalCumulativeRefundQty >= (totalOriginalQty - EPSILON)) {
                    if (previousRefundQty < (totalOriginalQty - EPSILON)) {
                        orderPointsLost += parseFloat(rule.reward_point_amount || 0);
                    }
                }
            }
        }

        // 2. Account for points back from refunded rewards
        // Note: This part requires the actual card ID to know if the reward originated from this card
        if (loyaltyCard.id) {
            for (const line of refundedRewardLines) {
                const originalLine = line.refunded_orderline_id;
                if (originalLine.coupon_id?.id === loyaltyCard.id) {
                    orderPointsLost -= originalLine.points_cost;
                }
            }
        }

        return orderPointsLost;
    },

    deductLoyaltyPoints() {
        // Restricted to refund orders only - we only want 'Points Lost' display here.
        if (!this.getHasRefundLines()) {
            return [];
        }

        let partner = this.getPartner();
        if (!partner && this.refunded_order_id) {
            partner = this.refunded_order_id.getPartner();
        }
        if (!partner) {
            return [];
        }

        const partnerId = partner.id;
        const valsList = [];

        // Get all loyalty cards in the POS
        const allCards = this.models["loyalty.card"]?.getAll() || [];

        // 1. Primary discovery: filter by partner
        let loyaltyCards = allCards.filter((c) => {
            const cardPartnerId = c.partner_id?.id ?? c.partner_id;
            return cardPartnerId === partnerId;
        });

        // 2. Fallback discovery: if partner filtering fails (e.g. state transition), 
        // try to find cards referenced directly in this order's refund lines.
        if (loyaltyCards.length === 0) {
            const setOfCardIds = new Set();
            for (const line of this.getOrderlines()) {
                if (line.refunded_orderline_id?.coupon_id?.id) {
                    setOfCardIds.add(line.refunded_orderline_id.coupon_id.id);
                }
            }
            if (setOfCardIds.size > 0) {
                loyaltyCards = allCards.filter(c => setOfCardIds.has(c.id));
            }
        }

        for (const loyaltyCard of loyaltyCards) {
            const program = loyaltyCard.program_id;
            if (!program || program.program_type !== "loyalty") {
                continue;
            }

            // Points lost in THIS order
            const pointsLostForThisOrder = this._calculateOrderDeductions(this, loyaltyCard);

            // Only include programs that have a deduction in the current refund order
            if (pointsLostForThisOrder <= 0) {
                continue;
            }

            /**
             * Aggregation Strategy for Balance:
             * Although we hide 'Balance' on the receipt now, we still calculate it 
             * to provide accurate session-aware tracking for internal logic.
             */
            let sessionNetChange = 0;
            const sessionOrders = this.models["pos.order"].filter(o =>
                o.finalized && (o.partner_id?.id ?? o.partner_id) === partnerId
            );

            for (const order of sessionOrders) {
                if (order.isSynced || order === this) {
                    continue;
                }
                if (!order.getHasRefundLines()) {
                    const orderLoyaltyStats = order.getLoyaltyPoints();
                    const orderStat = orderLoyaltyStats.find(s => s.couponId == loyaltyCard.id);
                    if (orderStat) {
                        sessionNetChange += (orderStat.points.won || 0) - (orderStat.points.spent || 0);
                    }
                } else {
                    sessionNetChange -= this._calculateOrderDeductions(order, loyaltyCard);
                }
            }

            const syncedBalance = parseFloat(loyaltyCard.points || 0);
            const realTimeBalance = syncedBalance + sessionNetChange - pointsLostForThisOrder;

            valsList.push({
                lostPoint: parseFloat(pointsLostForThisOrder.toFixed(2)),
                newPoint: parseFloat(realTimeBalance.toFixed(2)),
                programName: program.name || "Loyalty Program",
                isRefund: true,
                ruleId: (program.rule_ids || []).map(r => r.id).join(","),
            });
        }
        return valsList;
    },

    _getRewardLineValues(args) {
        //---added the new reward type to this function----
        const reward = args["reward"];
        if (reward.reward_type === "discount") {
            return this._getRewardLineValuesDiscount(args);
        } else if (reward.reward_type === "product") {
            return this._getRewardLineValuesProduct(args);
        } else if (reward.reward_type === "redemption") {
            return this._getRewardLineValuesRedemption(args)
        }
    },

    _getRewardLineValuesRedemption(args) {
        //---Reward product for the reward 'redemption'---
        const reward = args["reward"];
        const coupon_id = args["coupon_id"];

        let { discountable } = this._getDiscountableOnOrder(reward);
        discountable = Math.min(this.priceIncl, discountable);

        const pointsToRedeem = reward.pointsToRedeem || 0;
        let discount = pointsToRedeem * (reward.redemption_amount || 0);

        // Cap by max_redemption_amount if set
        if (reward.max_redemption_amount > 0) {
            discount = Math.min(discount, reward.max_redemption_amount);
        }

        // Cannot discount more than available
        discount = Math.min(discount, discountable);

        const discountProduct = reward.discount_line_product_id || reward.program_id.reward_product_id;
        const rewardCode = _newRandomRewardCode();
        const points = this._getRealCouponPoints(coupon_id);
        const cost = reward.clear_wallet ? points : pointsToRedeem;

        return [
            {
                product_id: discountProduct,
                price_unit: -discount,
                qty: 1,
                reward_id: reward,
                is_reward_line: true,
                _reward_product_id: discountProduct,
                coupon_id: coupon_id,
                points_cost: cost,
                reward_identifier_code: rewardCode,
                tax_ids: discountProduct?.taxes_id,
            },
        ];
    },

    pointsForPrograms(programs) {
        const result = super.pointsForPrograms(...arguments);
        if (!this.getHasRefundLines()) {
            return result;
        }

        // Apply our custom deduction logic for refunds
        for (const program of programs) {
            if (program.program_type !== "loyalty") {
                continue;
            }

            // We calculate points lost per PROGRAM. 
            // This ensures points are deducted even if the card isn't in POS cache yet.
            const pointsLost = this._calculateOrderDeductions(this, { program_id: program });

            if (pointsLost > 0) {
                if (!result[program.id] || result[program.id].length === 0) {
                    result[program.id] = [{ points: 0 }];
                }
                // Subtract the loss. If Odoo incorrectly awarded points (e.g. +10 for refund)
                // this will correctly bring it down to the intended negative value (-10).
                result[program.id][0].points -= pointsLost;
            }
        }
        return result;
    },

    get change() {
        //----Change is modified when change is added to loyalty points----
        // When change has been converted to loyalty points, report 0 change
        if (this.changeConverted !== undefined) {
            return 0;
        }
        // Fall back to the Odoo 19 built-in `change` getter from PosOrderAccounting
        return super.change;
    },
});

patch(PosStore.prototype, {
    async updatePrograms() {
        await super.updatePrograms();
        const order = this.getOrder();
        if (order && (order.is_refund || order.getHasRefundLines())) {
            for (const pe of Object.values(order.uiState.couponPointChanges)) {
                // FIXED: Standard Odoo 19 has two critical bugs here:
                // 1. It incorrectly awards "points per order" for refunds.
                // 2. It has a bad split("-") logic that fails for negative numbers.

                const program = this.models["loyalty.program"].get(pe.program_id);
                if (program && program.program_type === "loyalty") {
                    const pointsLost = order._calculateOrderDeductions(order, { program_id: program });
                    if (pointsLost > 0) {
                        // Ensure the points are negative. 
                        // If Odoo mistakenly calculated +10, we force it to -10.
                        if (pe.points >= 0) {
                            pe.points = -pointsLost;
                        }
                    }
                }
            }
        }
    },

    async postProcessLoyalty(order) {
        // Compile data for our function
        const ProgramModel = this.models["loyalty.program"];
        const rewardLines = order._get_reward_lines();
        const partner = order.getPartner();
        let couponData = Object.values(order.uiState.couponPointChanges).reduce((agg, pe) => {
            agg[pe.coupon_id] = Object.assign({}, pe, {
                points: pe.points - order._getPointsCorrection(ProgramModel.get(pe.program_id)),
            });
            const program = ProgramModel.get(pe.program_id);
            if (
                (program.is_nominative || program.program_type == "next_order_coupons") &&
                partner
            ) {
                agg[pe.coupon_id].partner_id = partner.id;
            }
            if (program.program_type != "loyalty") {
                agg[pe.coupon_id].expiration_date = program.date_to || pe.expiration_date;
            }
            return agg;
        }, {});
        for (const line of rewardLines) {
            const reward = line.reward_id;
            const couponId = line.coupon_id.id;
            if (!couponData[couponId]) {
                couponData[couponId] = {
                    points: 0,
                    program_id: reward.program_id.id,
                    coupon_id: couponId,
                    barcode: false,
                };
                if (reward.program_type != "loyalty") {
                    couponData[couponId].expiration_date = reward.program_id.date_to;
                }
            }
            if (!couponData[couponId].line_codes) {
                couponData[couponId].line_codes = [];
            }
            if (!couponData[couponId].line_codes.includes(line.reward_identifier_code)) {
                couponData[couponId].line_codes.push(line.reward_identifier_code);
            }
            couponData[couponId].points -= line.points_cost;
        }

        // PATCH: Ensure point changes are synced even if there are no reward lines
        // This is critical for refunds where points are deducted but no rewards are redeemed/refunded.
        couponData = Object.fromEntries(
            Object.entries(couponData)
                .filter(([key, value]) => {
                    const program = ProgramModel.get(value.program_id);
                    if (program.applies_on === "current") {
                        // Allow sync if there are reward lines OR if there's a non-zero point change
                        return (value.line_codes && value.line_codes.length) || value.points !== 0;
                    }
                    return true;
                })
                .map(([key, value]) => [key, omit(value, "appliedRules")])
        );

        if (Object.keys(couponData || {}).length > 0) {
            const payload = await this.data.call("pos.order", "confirm_coupon_programs", [
                order.id,
                couponData,
            ]);
            if (payload.coupon_updates) {
                for (const couponUpdate of payload.coupon_updates) {
                    if (couponUpdate.old_id == couponUpdate.id) {
                        const coupon = this.models["loyalty.card"].get(couponUpdate.id);
                        if (!coupon) {
                            await this.data.read("loyalty.card", [couponUpdate.id]);
                        } else {
                            coupon.points = couponUpdate.points;
                        }
                    } else {
                        const coupon = this.models["loyalty.card"].create({
                            id: couponUpdate.id,
                            code: couponUpdate.code,
                            program_id: this.models["loyalty.program"].get(couponUpdate.program_id),
                            partner_id: this.models["res.partner"].get(couponUpdate.partner_id),
                            points: couponUpdate.points,
                        });
                        for (const line of order.lines) {
                            if (line.coupon_id?.id == couponUpdate.old_id) {
                                line.coupon_id = coupon;
                            }
                        }
                        this.models["loyalty.card"].get(couponUpdate.old_id)?.delete();
                    }
                }
            }
            if (payload.program_updates) {
                for (const programUpdate of payload.program_updates) {
                    const program = ProgramModel.get(programUpdate.program_id);
                    if (program) {
                        program.total_order_count = programUpdate.usages;
                    }
                }
            }
            if (payload.coupon_report && Object.keys(payload.coupon_report).length > 0) {
                for (const [actionId, active_ids] of Object.entries(payload.coupon_report)) {
                    await this.env.services.report.doAction(actionId, active_ids);
                }
                order.has_pdf_gift_card = Object.keys(payload.coupon_report).length > 0;
            }
            if (payload.new_coupon_info?.length) {
                order.new_coupon_info = payload.new_coupon_info;
            }
        }
    },
});