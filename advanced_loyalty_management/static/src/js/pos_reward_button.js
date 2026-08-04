/** @odoo-module **/

import { RewardPopup } from "@advanced_loyalty_management/app/loyalty_program/pos_reward_redeem_popup";
import { patch } from "@web/core/utils/patch";
import { SelectionPopup } from "@point_of_sale/app/components/popups/selection_popup/selection_popup";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { _t } from "@web/core/l10n/translation";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { useService } from "@web/core/utils/hooks";
import { onWillUpdateProps, onWillRender } from "@odoo/owl";

patch(ControlButtons.prototype, {
    setup() {
        super.setup(...arguments);
        this.notification = useService("notification");
        // Ensure state exists and initialize frequency
        if (this.state) {
            this.state.frequency = 0;
        } else {
            console.warn("ControlButtons: state not found during setup. Initializing local state.");
            this.state = useState({ frequency: 0 });
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
                const totalClaimed = result[1].length;
                this.state.frequency = totalClaimed;
            }
        } catch (e) {
            console.error("Error updating redemption frequency:", e);
        }
    },

    getPotentialRewards() {
        const order = this.currentOrder;
        let rewards = [];
        if (order) {
            const claimableRewards = order.getClaimableRewards();
            rewards = claimableRewards.filter(
                ({ reward }) => reward.program_id.program_type !== "ewallet"
            );
        }

        const result = {};
        const discountRewards = rewards.filter(({ reward }) => reward.reward_type == "discount");
        const freeProductRewards = rewards.filter(({ reward }) => reward.reward_type == "product");

        // Custom redemption logic - ensures fields exist and condition is met
        const redemptionRewards = rewards.filter(({ reward }) => {
            const freq = reward.redemption_frequency || 0;
            const currentFreq = this.state.frequency || 0;
            return (
                reward.reward_type == "redemption" &&
                (order.priceExcl || 0) > 0 &&
                freq > currentFreq
            );
        });

        const potentialFreeProductRewards = this.pos.getPotentialFreeProductRewards();
        const avaiRewards = [
            ...potentialFreeProductRewards,
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
        order.uiState.disabledRewards.delete(reward.id);
        const args = {};

        if (reward.reward_type === "product" && reward.multi_product) {
            const productsList = reward.reward_product_ids.map((product_id) => ({
                id: product_id.id,
                label: product_id.display_name,
                item: product_id,
            }));
            const selectedProduct = await makeAwaitable(this.dialog, SelectionPopup, {
                title: _t("Please select a product for this reward"),
                list: productsList,
            });
            if (!selectedProduct) {
                return false;
            }
            args["product"] = selectedProduct;
        }

        if ((reward.reward_type == "product" && reward.program_id.applies_on !== "both") ||
            (reward.program_id.applies_on == "both" && potentialQty)
        ) {
            const product = args["product"] || reward.reward_product_ids[0];
            await this.pos.addLineToCurrentOrder(
                {
                    product_id: product,
                    product_tmpl_id: product.product_tmpl_id,
                    qty: potentialQty || 1,
                },
                {}
            );
            return true;
        } else {
            const result = order._applyReward(reward, coupon_id, args);
            if (result !== true) {
                this.notification.add(result, { type: "danger" });
            }
            this.pos.updateRewards();
            return result;
        }
    },

    async clickRewards() {
        const rewards = this.getPotentialRewards();
        const order = this.currentOrder;
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
                getPayload: (selectedReward) => {
                    if (selectedReward.reward.reward_type == "redemption") {
                        let maxPoints = 0;
                        if (selectedReward.reward.max_redemption_type == 'points') {
                            maxPoints = selectedReward.reward.max_redemption_amount / (selectedReward.reward.redemption_amount || 1);
                        } else if (selectedReward.reward.max_redemption_type == 'amount') {
                            maxPoints = selectedReward.reward.max_redemption_amount / (selectedReward.reward.redemption_amount || 1);
                        } else if (selectedReward.reward.max_redemption_type == 'percent') {
                            const maxRedemptionAmt = (order.priceIncl * selectedReward.reward.max_redemption_amount) / 100;
                            maxPoints = maxRedemptionAmt / (selectedReward.reward.redemption_amount || 1);
                        }

                        this.dialog.add(RewardPopup, {
                            title: _t("Redeem Points"),
                            rewards: rewards,
                            selected_reward: selectedReward,
                            order: order,
                            max_redemption_points: maxPoints,
                            property: this,
                            coupon_id: selectedReward.coupon_id, // Corrected from order.coupon_id
                        });
                    } else {
                        this._applyReward(
                            selectedReward.reward,
                            selectedReward.coupon_id,
                            selectedReward.potentialQty
                        );
                    }
                },
            });
        }
    },
});
