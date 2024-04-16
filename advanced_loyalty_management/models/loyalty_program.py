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
    """To set the point rate when change is converted to loyalty points"""
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
    def convert_loyalty(self, pid, cid, loyalty, partner_id):
        """converting the change to loyalty points"""
        if int(cid[0]) < 0:
            self.env['loyalty.card'].create({
                'program_id': pid[0],
                'partner_id': partner_id[0],
                'points': loyalty[0]
            })

        else:
            loyalty_card = self.env['loyalty.card'].search(
                [('id', '=', int(cid[0]))])
            loyalty_card.points += loyalty[0]
