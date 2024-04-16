# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, models, fields


class LoyaltyReward(models.Model):
    """To create new reward type """
    _inherit = 'loyalty.reward'

    reward_type = fields.Selection(selection_add=[('redemption', 'Redemption')],
                                   ondelete={'redemption': 'cascade'},
                                   help="Reward Type")
    redemption_point = fields.Integer(string='Redemption Point', default=1.0,
                                      readonly=True,
                                      help="No of points redeemed according "
                                           "to the redemption amount")
    redemption_amount = fields.Float(string='Maximum Redemption per Point',
                                     default=1.00, required=True,
                                     help="Maximum Redemption per redemption "
                                          "point")
    max_redemption_type = fields.Selection(
        [('amount', 'Amount'), ('percent', 'Percentage'), ('points', 'Points')],
        default="amount",
        required=True,
        help="Redemption type based on Fixed Amount,percentage or Point wise")
    max_redemption_amount = fields.Float(string='Max Redemption Amount',
                                         default=10, required=True,
                                         help="Maximum redemption amount "
                                              "given to an order")
    redemption_frequency = fields.Integer(string='Redemption Frequency',
                                          default=1, required=True,
                                          help="Number of times this reward "
                                               "can be claimed")
    redemption_frequency_unit = fields.Selection([('day', 'Daily'),
                                                  ('week', 'Weekly'),
                                                  ('month', 'Monthly'),
                                                  ('year', 'Yearly')],
                                                 default='day', required=True,
                                                 string='Redemption Frequency'
                                                        'Unit',
                                                 help="Choose the frequency "
                                                      "for claiming the reward")
    redemption_eligibility = fields.Float(string="Redemption Eligibility",
                                          default=200,
                                          help="points required for claiming "
                                               "the reward")

    @api.depends('reward_type', 'reward_product_id', 'discount_mode',
                 'discount', 'currency_id', 'discount_applicability',
                 'all_discount_product_ids')
    def _compute_description(self):
        """compute description when the reward type is redemption"""
        for reward in self:
            if reward.reward_type == 'redemption':
                reward.description = 'Redemption'
            else:
                res = super(LoyaltyReward,
                            self)._compute_description()
                return res
