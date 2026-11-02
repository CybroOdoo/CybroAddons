/** @odoo-module **/

import { RewardPopup } from "@advanced_loyalty_management/app/loyalty_program/pos_reward_redeem_popup";
import { patch } from "@web/core/utils/patch";
import { SelectionPopup } from "@point_of_sale/app/components/popups/selection_popup/selection_popup";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { _t } from "@web/core/l10n/translation";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { useService } from "@web/core/utils/hooks";
import { onWillUpdateProps, onWillRender, proxy } from "@odoo/owl";

patch(ControlButtons.prototype, {
    setup() {
        super.setup(...arguments);
        this.notification = useService("notification");
        // Ensure state exists and initialize frequency
        if (this.state) {
            this.state.frequency = 0;
            this.state.redemptionDates = [];
        } else {
            this.state = proxy({ frequency: 0, redemptionDates: [] });
        }

        // Trigger frequency check before rendering if the partner has changed
        onWillRender(async () => {
            const order = this.currentOrder;
            const partner = order ? order.getPartner() : null;
            if (partner && partner.id !== this._lastPartnerId) {
                this._lastPartnerId = partner.id;
                await this.updateFrequency();
            } else if (!partner) {
                this._lastPartnerId = null;
                this.state.frequency = 0;
                this.state.redemptionDates = [];
            }
        });
    },

    async updateFrequency() {
        const order = this.currentOrder;
        const partner = order ? order.getPartner() : null;
        if (!partner) return;

        try {
            const result = await this.env.services.orm.call("res.partner", "check_redemption", [[partner.id]]);
            if (result && result[1]) {
                this.state.redemptionDates = result[1];
                this.state.frequency = result[1].length;
            } else {
                this.state.redemptionDates = [];
                this.state.frequency = 0;
            }
        } catch {
            // Keep existing frequency if check fails
        }
    },

    getRedemptionFrequency(reward) {
        const dates = this.state.redemptionDates || [];
        if (!dates.length) return 0;
        const unit = reward.redemption_frequency_unit || "day";
        const now = new Date();

        return dates.filter((dStr) => {
            const d = new Date(dStr);
            if (isNaN(d.getTime())) return false;
            if (unit === "day") {
                return (
                    d.getFullYear() === now.getFullYear() &&
                    d.getMonth() === now.getMonth() &&
                    d.getDate() === now.getDate()
                );
            } else if (unit === "week") {
                const diffTime = Math.abs(now.getTime() - d.getTime());
                const diffDays = diffTime / (1000 * 60 * 60 * 24);
                return diffDays <= 7;
            } else if (unit === "month") {
                return (
                    d.getFullYear() === now.getFullYear() &&
                    d.getMonth() === now.getMonth()
                );
            } else if (unit === "year") {
                return d.getFullYear() === now.getFullYear();
            }
            return false;
        }).length;
    },

    getPotentialRewards() {
        const order = this.currentOrder;
        let rewards = [];
        if (order) {
            const claimableRewards = order.availableRewards;
            rewards = claimableRewards.filter(
                ({ reward }) => reward.program_id.program_type !== "ewallet"
            );
        }

        const result = {};
        const discountRewards = rewards.filter(({ reward }) => reward.reward_type == "discount");
        const freeProductRewards = rewards.filter(({ reward }) => reward.reward_type == "product");

        // Custom redemption logic - respects frequency unit and eligibility
        const redemptionRewards = rewards.filter(({ reward }) => {
            const freq = reward.redemption_frequency || 0;
            const currentFreq = this.getRedemptionFrequency(reward);
            const program = reward.program_id;
            const card = this.pos.models["loyalty.card"]?.find(
                (c) =>
                    c.program_id?.id === program?.id &&
                    c.partner_id?.id === order.partner_id?.id
            );
            const cardPoints = card?.points || 0;
            const minEligibility = reward.redemption_eligibility || 0;

            return (
                reward.reward_type === "redemption" &&
                (order.priceExcl || 0) > 0 &&
                freq > currentFreq &&
                cardPoints >= minEligibility
            );
        });

        const avaiRewards = [
            ...discountRewards,
            ...freeProductRewards,
            ...redemptionRewards,
        ];

        for (const reward of avaiRewards) {
            result[reward.reward.id] = reward;
        }
        return Object.values(result);
    },

    async _applyReward(reward, coupon_id, potentialQty) {
        const order = this.currentOrder;
        const args = {};
        if (reward.reward_type === "redemption") {
            const pointsToRedeem = reward.pointsToRedeem || 0;

            if (pointsToRedeem <= 0) {
                return false;
            }

            let discountable = order
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
                        total + order.getLineDiscountablePrice(line.uuid),
                    0
                );

            discountable = Math.min(order.priceIncl, discountable);

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
                        (order.priceIncl * reward.max_redemption_amount) / 100;

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

            if (!discountProduct) {
                return false;
            }

            const program = reward.program_id;

            const cards = this.pos.models["loyalty.card"].filter(
                (card) => card.program_id?.id === program.id
            );
            const card = cards.find(
                (card) => card.partner_id?.id === order.partner_id?.id
            );
            const cardPoints = card?.points || 0;
            if (pointsToRedeem > cardPoints) {
                return false;
            }

            const rewardLine = this.pos.models["pos.order.line"].create({
                card_id: card || undefined,
                product_id: discountProduct,
                price_unit: -discount,
                qty: 1,
                reward_id: reward,
                is_reward_line: true,
                points_cost: pointsToRedeem,
                order_id: order,
            });

            this.pos.selectOrderLine(order, rewardLine);
            return true;
        }

        return super._applyReward(...arguments);
    },

    async clickRewards() {
        const order = this.pos.getOrder();
        const rewards = this.getPotentialRewards();

        if (rewards.length >= 1) {
            const rewardsList = rewards.map((reward) => ({
                id: reward.reward.id,
                label: reward.reward.program_id.name,
                description: `Add "${reward.reward.description}"`,
                item: reward,
            }));

            this.dialog.add(SelectionPopup, {
                title: _t("Available rewards"),
                list: rewardsList,

                getPayload: async (selectedReward) => {
                    const reward = selectedReward.reward;
                    const programId = reward.program_id?.id;

                    if (order.disabled_program_ids.includes(programId)) {
                        order.disabled_program_ids =
                            order.disabled_program_ids.filter(
                                (id) => id !== programId
                            );

                        if (
                            order.appliedPrograms.some(
                                (program) => program.id === programId
                            )
                        ) {
                            order.recomputeRewards();

                            if (order._selectRewardLine(reward)) {
                                this.numberBuffer.reset();
                            }

                            return;
                        }
                    }
                    if (reward.reward_type === "redemption") {
                        const program = reward.program_id;
                        const cards = this.pos.models["loyalty.card"].filter(
                            (c) => c.program_id?.id === program?.id
                        );
                        const card = cards.find(
                            (c) => c.partner_id?.id === order.partner_id?.id
                        );
                        const cardPoints = card ? card.points : 0;

                        let maxPoints = 0;

                        if (reward.max_redemption_type === "points") {
                            maxPoints = reward.max_redemption_amount || 0;
                        } else if (reward.max_redemption_type === "amount") {
                            maxPoints =
                                (reward.max_redemption_amount || 0) /
                                (reward.redemption_amount || 1);
                        } else if (reward.max_redemption_type === "percent") {
                            const maxRedemptionAmt =
                                ((order.priceIncl || 0) *
                                    (reward.max_redemption_amount || 0)) /
                                100;

                            maxPoints =
                                maxRedemptionAmt /
                                (reward.redemption_amount || 1);
                        }

                        if (cardPoints > 0) {
                            maxPoints = maxPoints > 0 ? Math.min(maxPoints, cardPoints) : cardPoints;
                        } else {
                            maxPoints = 0;
                        }
                        maxPoints = Math.floor(maxPoints);

                        this.dialog.add(RewardPopup, {
                            title: _t("Redeem Points"),
                            rewards: rewards,
                            selected_reward: selectedReward,
                            order: order,
                            max_redemption_points: maxPoints,
                            property: this,
                        });

                        return;
                    }
                    let reward_product_id;

                    if (reward.multi_product) {
                        reward_product_id = await makeAwaitable(
                            this.dialog,
                            SelectionPopup,
                            {
                                title: _t(
                                    "Please select a product for this reward"
                                ),
                                list: reward.reward_product_ids.map(
                                    (product) => ({
                                        id: product.id,
                                        item: product,
                                        label: product.display_name,
                                    })
                                ),
                            }
                        );

                        if (!reward_product_id) {
                            return;
                        }
                    }

                    order.active_rewards.push({
                        reward_id: reward.id,
                        reward_product_id,
                    });

                    order.recomputeRewards();

                    if (order._selectRewardLine(reward)) {
                        this.numberBuffer.reset();
                    }
                },
            });
        }
    },
});
