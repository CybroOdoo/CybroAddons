/** @odoo-module **/

import { RewardPopup } from "@advanced_loyalty_management/js/pos_reward_redeem_popup";
import { patch } from "@web/core/utils/patch";
import { SelectionPopup } from "@point_of_sale/app/utils/input_popups/selection_popup";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { RewardButton } from "@pos_loyalty/app/control_buttons/reward_button/reward_button";
import { _t } from "@web/core/l10n/translation";
import { useState } from "@odoo/owl";

patch(RewardButton.prototype,{
    setup(){
        super.setup()
        this.state = useState({
            frequency : 0,
        });
    },

    _mergeFreeProductRewards(freeProductRewards, potentialFreeProductRewards,redemption) {
    //---reward type redemption is shown in list of rewards
        const result = [];
        for (const reward of potentialFreeProductRewards) {
            if (!freeProductRewards.find((item) => item.reward.id === reward.reward.id)) {
                result.push(reward);
            }
        }
        for (const rew of redemption){
            result.push(rew)
        }
        return freeProductRewards.concat(result);
    },

     _getBaseCouponBalance(couponId) {
        return this.pos.couponCache[couponId]?.balance || 0;
    },

     _hasBaseBalanceForReward(reward, couponId) {
        const baseBalance = this._getBaseCouponBalance(couponId);
        if (reward.clear_wallet) {
            return baseBalance > 0;
        }
        return baseBalance >= (reward.required_points || 0);
    },

     _getPotentialRewards() {
     //---Reward type redemption is included in the list of claimable rewards---
        const order = this.pos.get_order();
        let rewards = [];
        if (order) {
            const claimableRewards = order.getClaimableRewards();
            rewards = claimableRewards.filter(
                ({ reward }) => reward.program_id.program_type !== "ewallet"
            );
        }
        var pointCheck = false
        for (const pointChange of Object.values(order.couponPointChanges)){
            if(pointChange.coupon_id > 0){
                pointCheck = true
            }
        }
        const discountRewards = rewards.filter(({ reward, coupon_id }) =>
            reward.reward_type == "discount" &&
            this._hasBaseBalanceForReward(reward, coupon_id)
        );
        const freeProductRewards = rewards.filter(({ reward }) => reward.reward_type == "product");
        const redemption = rewards.filter(({ reward, coupon_id }) => {
        if (reward.reward_type != "redemption") {
            return false;
        }
        return reward.max_redemption_amount < order.get_subtotal() &&
        pointCheck == true &&
        reward.redemption_frequency > this.state.frequency &&
        this._getBaseCouponBalance(coupon_id) >= (reward.redemption_eligibility || 0);
        });
        const potentialFreeProductRewards = this.pos.getPotentialFreeProductRewards()
        return discountRewards.concat(
            this._mergeFreeProductRewards(freeProductRewards, potentialFreeProductRewards,redemption))
    },

    async _getRedemptionFrequencyCount(reward) {
        const partner = this.pos.get_order()?.partner;
        if (!partner) {
            return 0;
        }
        return await this.env.services.orm.call(
            "res.partner",
            "get_redemption_frequency_count",
            [partner.id, reward.redemption_frequency_unit]
        );
    },

     async click() {
    //---choose the reward ---
        const rewards = this._getPotentialRewards();
        const order = this.pos.get_order();
        if (rewards.length >= 1) {
            const rewardsList = rewards.map((reward) => ({
                id: reward.reward.id,
                label: reward.reward.description,
                description: reward.reward.program_id.name,
                item: reward,
            }));
            const { confirmed, payload: selectedReward } = await this.popup.add(SelectionPopup, {
                title: _t("Please select a reward"),
                list: rewardsList,
            });
            if (confirmed) {
            if(selectedReward.reward.reward_type == "redemption"){
            const frequencyCount = await this._getRedemptionFrequencyCount(selectedReward.reward);
            this.state.frequency = frequencyCount;
            if (frequencyCount >= selectedReward.reward.redemption_frequency) {
                await this.popup.add(ErrorPopup, {
                    body: _t("This reward has already reached its redemption frequency limit for the current period."),
                });
                return false;
            }
            var points = []
            if(selectedReward.reward.max_redemption_type == 'points'){
                points.push(selectedReward.reward.max_redemption_amount/selectedReward.reward.redemption_amount)
            }
            else if(selectedReward.reward.max_redemption_type == 'amount'){
                points.push(selectedReward.reward.max_redemption_amount/selectedReward.reward.redemption_amount)
            }
            else if(selectedReward.reward.max_redemption_type == 'percent'){
                var totalAmount = order.get_total_with_tax()
                var maxRedemption = totalAmount * selectedReward.reward.max_redemption_amount / 100
                points.push(maxRedemption/selectedReward.reward.redemption_amount)
            }
            await this.popup.add(RewardPopup, {
                   title: _t("Redeem Points"),
                   rewards: rewards,
                   selected_reward: selectedReward,
                   order: order,
                   max_redemption_points: points[0],
                   min_redemption_points: selectedReward.reward.min_redemption_amount || 0,
                   property: this
            });
            }
            else{
                var cost = selectedReward.reward.required_points
                order.selectedCoupon = selectedReward.coupon_id
                order.pointsCost = cost
                return this._applyReward(
                    selectedReward.reward,
                    selectedReward.coupon_id,
                    selectedReward.potentialQty
                );
                }
            }
        }
        return false;
    },
})

