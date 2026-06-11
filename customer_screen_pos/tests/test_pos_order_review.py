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
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPosOrderReview(TransactionCase):
    """Test pos.order.review records."""

    def test_pos_order_review_creation(self):
        """POS order review records store customer feedback values."""
        review = self.env['pos.order.review'].create({
            'review_text': 'Very good service',
            'review_star': 'star5',
            'pos_session': 10,
            'partner': 20,
            'pos_order_ref': 'Order 0001',
        })

        self.assertEqual(review.review_text, 'Very good service')
        self.assertEqual(review.review_star, 'star5')
        self.assertEqual(review.pos_session, 10)
        self.assertEqual(review.partner, 20)
        self.assertEqual(review.pos_order_ref, 'Order 0001')
