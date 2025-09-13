/** @odoo-module **/

import { RewardPopup } from "@advanced_loyalty_management/js/pos_reward_redeem_popup";
import { patch } from "@web/core/utils/patch";
import { SelectionPopup } from "@point_of_sale/app/utils/input_popups/selection_popup";
import { RewardButton } from "@pos_loyalty/app/control_buttons/reward_button/reward_button";
import { _t } from "@web/core/l10n/translation";
import { session } from "@web/session";
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

     _getPotentialRewards() {
     //---Reward type redemption is included in the list of claimable rewards---
        const order = this.pos.get_order();
        const partner_id = this.pos.get_order().partner
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
        const discountRewards = rewards.filter(({ reward }) => reward.reward_type == "discount");
        const freeProductRewards = rewards.filter(({ reward }) => reward.reward_type == "product");
        const redemption = rewards.filter(({ reward }) => reward.reward_type == "redemption" &&
        reward.max_redemption_amount < order.get_subtotal() &&
        pointCheck == true
        && reward.redemption_frequency > this.state.frequency
        );
        if(order.partner != null){
            var checkFrequency =  this.check(rewards)
        }
        const potentialFreeProductRewards = this.pos.getPotentialFreeProductRewards()
        return discountRewards.concat(
            this._mergeFreeProductRewards(freeProductRewards, potentialFreeProductRewards,redemption))
    },

    async check(rewards){
    //---gives the number of times the reward is claimed---
        let count = 0;
        const partner_id = this.pos.get_order().partner.id
            var checkRedemption = await this.env.services.orm.call("res.partner","check_redemption",[[partner_id]]).then((result) =>{
        const today = new Date()
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        const formattedDate = `${year}-${month}-${day}`;
        const currentWeekStart = new Date(today.getFullYear(), today.getMonth(), today.getDate() - today.getDay());
        const currentWeekEnd = new Date(today.getFullYear(), today.getMonth(), today.getDate() + (6 - today.getDay()));
        const formattedCurrentWeekStart = currentWeekStart.toISOString().split('T')[0];
        const formattedCurrentWeekEnd = currentWeekEnd.toISOString().split('T')[0];
        const currentMonthStart = new Date(today.getFullYear(), today.getMonth(), 1);
        const currentMonthEnd = new Date(today.getFullYear(), today.getMonth() + 1, 0); // Last day of current month
        const formattedCurrentMonthStart = currentMonthStart.toISOString().split('T')[0];
        const formattedCurrentMonthEnd = currentMonthEnd.toISOString().split('T')[0];
        const currentYearStart = new Date(today.getFullYear(), 0, 1);
        const currentYearEnd = new Date(today.getFullYear(), 11, 31);
        const formattedCurrentYearStart = currentYearStart.toISOString().split('T')[0];
        const formattedCurrentYearEnd = currentYearEnd.toISOString().split('T')[0];
        for (const reward of rewards){
        if(reward.reward.redemption_frequency_unit === 'day'){
            for (let i = 0; i < result[1].length; i++) {
                if (result[1][i] === formattedDate) {
                    count ++;
                }
            }
        }
        else if(reward.reward.redemption_frequency_unit === 'week'){
            for (let i = 0; i < result[1].length; i++) {
                const date =(result[1][i]);
                if (date >= formattedCurrentWeekStart && date <= formattedCurrentWeekEnd) {
                    count++;
                }
            }
        }
        else if(reward.reward.redemption_frequency_unit === 'month'){
            for (let i = 0; i < result[1].length; i++) {
                const date =(result[1][i]);
                if (date >= formattedCurrentMonthStart && date <= formattedCurrentMonthEnd) {
                    count++;
                }
            }
        }
        else if(reward.reward.redemption_frequency_unit === 'year'){
            for (let i = 0; i < result[1].length; i++) {
                const date =(result[1][i]);
                if (date >= formattedCurrentYearStart && date <= formattedCurrentYearEnd) {
                    count ++

                }
            }
        }
        }
        return count
        });
        this.state.frequency = checkRedemption
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
                   max_redemption_points : points[0],
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

