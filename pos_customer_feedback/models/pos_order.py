# -*- coding: utf-8 -*-
#############################################################################
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
#############################################################################
from odoo import api, fields, models


class PosOrder(models.Model):
    """To add feedback fields and store its value in pos order"""
    _inherit = "pos.order"

    customer_feedback = fields.Integer(string='Customer Feedback', readonly=True,
                                        help="Customer rating (1-5 stars)")
    comment_feedback = fields.Text(string='Feedback Comments', readonly=True,
                                    help="Customer feedback comments")
    rating = fields.Char(string='Rating Display', help="Star rating display",
                         compute='_compute_rating', store=True)

    @api.depends('customer_feedback')
    def _compute_rating(self):
        """Display star rating based on customer_feedback value"""
        for order in self:
            if order.customer_feedback:
                order.rating = '\u2B50' * int(order.customer_feedback)
            else:
                order.rating = False
