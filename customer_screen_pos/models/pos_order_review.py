# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu KP (odoo@cybrosys.com)
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
from odoo import fields, models


class PoSOrderReview(models.Model):
    """PoSOrderReview provides option to store customers reviews for their
        POS orders in database"""
    _name = 'pos.order.review'
    _description = "POS Order Reviews"

    review_text = fields.Char(string="Review text",
                              help='To store review of customer'
                                   'from customer screen')
    review_star = fields.Char(string="Review Star",
                              help='To store rating of customer'
                                   'from customer screen')
    pos_session = fields.Integer(string="POS Session",
                                 help='To store session id of pos')
    partner = fields.Integer(string="Partner Id", help='for partner')
    pos_order_ref = fields.Char(string="POS Order Reference",
                                help='To store each order reference')
