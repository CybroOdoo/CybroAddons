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
from odoo.tests.common import TransactionCase
import logging

class TestPosOrderFeedback(TransactionCase):

    def test_01_rating_computation_with_feedback(self):
        """Test that the rating field correctly computes the star string based on customer_feedback integer."""

        # Create in-memory POS order record
        order = self.env['pos.order'].new({
            'customer_feedback': 5,
            'comment_feedback': 'Very good service!'
        })

        # Trigger compute method
        order._compute_rating()

        expected_rating = '\u2B50' * 5

        # Assertion
        self.assertEqual(
            order.rating,
            expected_rating,
            "The rating should display 4 stars."
        )

    def test_02_rating_computation_without_feedback(self):
        """Test that the rating field is correctly set to False when there is no feedback."""

        order = self.env['pos.order'].new({
            'customer_feedback': 0,
            'comment_feedback': ''
        })


        # Trigger compute method
        order._compute_rating()


        # Assertion
        self.assertFalse(
            order.rating,
            "The rating should be False when feedback is 0."
        )

    def test_03_rating_computation_max_stars(self):
        """Test that the rating field correctly displays 5 stars."""

        order = self.env['pos.order'].new({
            'customer_feedback': 5,
            'comment_feedback': 'Excellent!'
        })

        # Trigger compute method
        order._compute_rating()

        expected_rating = '\u2B50' * 5

        self.assertEqual(
            order.rating,
            expected_rating,
            "The rating should display 5 stars."
        )

