/** @odoo-module **/
import { Order, Orderline, PosGlobalState} from 'point_of_sale.models';
import Registries from 'point_of_sale.Registries';

var utils = require('web.utils');
var round_pr = utils.round_precision;

function _newRandomRewardCode() {
    return (Math.random() + 1).toString(36).substring(3);
}

const PosLoyaltyOrder = (Order) => class PosLoyaltyOrder extends Order {
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
                    won += this.pos.get_order().convertToLoyalty
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
    }

    _getRewardLineValues(args) {
        //----a new reward type is added
        const reward = args['reward'];
        if (reward.reward_type === 'discount') {
            return this._getRewardLineValuesDiscount(args);
        } else if (reward.reward_type === 'product') {
            return this._getRewardLineValuesProduct(args);
        }
        else if (reward.reward_type === 'redemption'){
            return this._getRewardLineValuesRedemption(args)
        }
        return [];
    }

    _getRewardLineValuesRedemption(args){
        //---configured new reward product
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
            tax_ids: [],
        },
        ]
    }
    get_change(paymentline) {
        //----change is converted to loyalty points
        if (!paymentline) {
            if(this.changeConverted == undefined){
                var change =
                this.get_total_paid() - this.get_total_with_tax() - this.get_rounding_applied();
            }
            else{
                var change = 0
            }
            } else {
                var change = -this.get_total_with_tax();
                var lines  = this.paymentlines;
                for (var i = 0; i < lines.length; i++) {
                    change += lines[i].get_amount();
                    if (lines[i] === paymentline) {
                        break;
                    }
                }
            }
        return round_pr(Math.max(0,change), this.pos.currency.rounding);
    }
    export_as_JSON() {
        //---amount returned is changed
        var orderLines, paymentLines;
        orderLines = [];
        this.orderlines.forEach(item => {
            return orderLines.push([0, 0, item.export_as_JSON()]);
        });
        paymentLines = [];
        this.paymentlines.forEach(_.bind( function(item) {
            return paymentLines.push([0, 0, item.export_as_JSON()]);
        }, this));
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
            creation_date: this.validation_date || this.creation_date, // todo: rename creation_date in master
            fiscal_position_id: this.fiscal_position ? this.fiscal_position.id : false,
            server_id: this.server_id ? this.server_id : false,
            to_invoice: this.to_invoice ? this.to_invoice : false,
            to_ship: this.to_ship ? this.to_ship : false,
            is_tipped: this.is_tipped || false,
            tip_amount: this.tip_amount || 0,
            access_token: this.access_token || '',
        };
        if (!this.is_paid && this.user_id) {
            json.user_id = this.user_id;
        }
        return json;
    }
}
Registries.Model.extend(Order, PosLoyaltyOrder);
