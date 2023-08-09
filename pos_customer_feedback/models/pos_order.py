# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Shafna K (odoo@cybrosys.com)
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
from odoo import api, fields, models


class PosOrder(models.Model):
    """To add feedback fields and store its value in pos order"""
    _inherit = "pos.order"

    feedback = fields.Char(string='Feedback', readonly=True,
                           help="Please provide your feedback")
    rating = fields.Char(string='Rating', help="Provide your ratings",
                         compute='_compute_rating')
    comment = fields.Text(string='Comments',  readonly=True,
                          help="Provide the feedbacks in comments")

    def _order_fields(self, ui_order):
        """To get the value of field in pos session to pos order"""
        res = super()._order_fields(ui_order)
        res['feedback'] = ui_order.get('customer_feedback')
        res['comment'] = ui_order.get('comment_feedback')
        return res

    @api.depends('feedback')
    def _compute_rating(self):
        """To print star in pos order based on the rating value
        choosing from pos session"""
        self.rating = False
        if self.feedback:
            self.rating = '\u2B50' * int(self.feedback)
