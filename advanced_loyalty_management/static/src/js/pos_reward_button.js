/** @odoo-module **/

import { RewardPopup } from "@advanced_loyalty_management/app/loyalty_program/pos_reward_redeem_popup";
import { patch } from "@web/core/utils/patch";
import { SelectionPopup } from "@point_of_sale/app/utils/input_popups/selection_popup";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { _t } from "@web/core/l10n/translation";
import { session } from "@web/session";
import { useState } from "@odoo/owl";

patch(ControlButtons.prototype,{
    setup(){
        super.setup()
        this.state = useState({
            frequency : 0,
        });
    },

    getPotentialRewards() {
        const order = this.pos.get_order();
        // Claimable rewards excluding those from eWallet programs.
        // eWallet rewards are handled in the eWalletButton.
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
        const redemption = rewards.filter(({ reward }) => reward.reward_type == "redemption" &&
        reward.max_redemption_amount < order.get_subtotal()
        && reward.redemption_frequency > this.state.frequency
        );
        if(order.partner_id){
            var checkFrequency =  this.check(rewards)
        }
        const potentialFreeProductRewards = this.pos.getPotentialFreeProductRewards();
        const avaiRewards = [
            ...potentialFreeProductRewards,
            ...discountRewards,
            ...freeProductRewards, // Free product rewards at the end of array to prioritize them
            ...redemption,
        ];

        for (const reward of avaiRewards) {
            result[reward.reward.id] = reward;
        }
        return Object.values(result);
    },

        async check(rewards){
        //---Gives the number of times the reward is claimed---
        let count = 0;
        const partner_id = this.pos.get_order().partner_id.id
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

    async _applyReward(reward, coupon_id, potentialQty) {
        const rewards = this.getPotentialRewards()
        const order = this.pos.get_order();
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
        if (
            (reward.reward_type == "product" && reward.program_id.applies_on !== "both") ||
            (reward.program_id.applies_on == "both" && potentialQty)
        ) {
            await this.pos.addLineToCurrentOrder(
                {
                    product_id: args["product"] || reward.reward_product_ids[0],
                    qty: potentialQty || 1,
                },
                {}
            );
            return true;
        }

        else {
            const result = order._applyReward(reward, coupon_id, args);
            if (result !== true) {
                // Returned an error
                this.notification.add(result);
            }
            this.pos.updateRewards();
            return result;
        }
    },
    async clickRewards() {
        const rewards = this.getPotentialRewards();
        const order = this.pos.get_order();
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
                         this.dialog.add(RewardPopup, {
                               title: _t("Redeem Points"),
                               rewards: rewards,
                               selected_reward: selectedReward,
                               order: order,
                               max_redemption_points : points[0],
                               property: this,
                               coupon_id: order.coupon_id,
                        });
                    }
                    else{
                        this._applyReward(
                        selectedReward.reward,
                        selectedReward.coupon_id,
                        selectedReward.potentialQty);
                    }
                },
            });
        }
    },
});
