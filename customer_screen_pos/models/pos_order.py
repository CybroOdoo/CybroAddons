# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import  fields, models


class PosOrder(models.Model):
    """Extend functionality of Point of Sale Order"""
    _inherit = 'pos.order'

    rating = fields.Selection([
        ('0', '0'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
    ], default='5', string="Rating", help="Rating Stars")
    rating_text = fields.Text(string="Feedback", help='Feedback of customers')


    def write(self, vals):
        """Overrides the default write method to update the POS order's rating and review text
            based on the corresponding `pos.order.review` record."""
        res = super().write(vals)
        for order in self:
            pos_order_review = self.env['pos.order.review'].sudo().search([
                ('pos_order_ref', '=', order.pos_reference)
            ], limit=1)
            if pos_order_review:
                vals_to_update = {
                    'rating': ("1" if pos_order_review.review_star == "star1" else
                               "2" if pos_order_review.review_star == "star2" else
                               "3" if pos_order_review.review_star == "star3" else
                               "4" if pos_order_review.review_star == "star4" else
                               "5"),
                    'rating_text': pos_order_review.review_text or '',
                }
                if (order.rating != vals_to_update['rating'] or
                        order.rating_text != vals_to_update['rating_text']):
                    super(PosOrder, order).write(vals_to_update)
        return res
