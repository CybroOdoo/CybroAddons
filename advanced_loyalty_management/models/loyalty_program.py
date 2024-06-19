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


class LoyaltyProgram(models.Model):
    """to load more fields in loyalty program and loyalty model"""
    _inherit = 'loyalty.program'

    point_rate = fields.Integer(string='Point Rate',
                                help="Points corresponding to each unit",
                                default=1, required=True)
    change_rate = fields.Monetary(string='Change Rate', default=1,
                                  readonly=True,
                                  help="Unit of money per points cost")
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda
                                      self: self.env.user.company_id.currency_id,
                                  help="Symbol of Currency")

    @api.model
    def convert_loyalty(self, program_id, coupon_id, added_loyalty, partner_id):
        """Change is converted to loyalty"""
        if int(coupon_id) < 0:
            self.env['loyalty.card'].create({
                'program_id': program_id,
                'partner_id': partner_id,
                'points': added_loyalty
            })
        else:
            loyalty_card = self.env['loyalty.card'].search(
                [('id', '=', int(coupon_id))])
            loyalty_card.points += added_loyalty
