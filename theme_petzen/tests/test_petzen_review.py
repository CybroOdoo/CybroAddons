# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from psycopg2 import IntegrityError

from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install', 'theme_petzen')
class TestPetzenReview(TransactionCase):
    """Test the moderation workflow and constraints of the customer review."""

    @classmethod
    def setUpClass(cls):
        """Create a pending review."""
        super().setUpClass()
        cls.review = cls.env['petzen.review'].create({
            'name': 'Jane Doe',
            'email': 'jane@example.com',
            'review': 'Great shop for my dog.',
        })

    def test_default_values(self):
        """A new review is pending and rated five stars."""
        self.assertEqual(self.review.state, 'pending')
        self.assertEqual(self.review.rating, 5)

    def test_action_approve(self):
        """Approving a review sets its state to approved."""
        self.review.action_approve()
        self.assertEqual(self.review.state, 'approved')

    def test_action_reject(self):
        """Rejecting a review sets its state to rejected."""
        self.review.action_reject()
        self.assertEqual(self.review.state, 'rejected')

    def test_action_reset_to_pending(self):
        """A moderated review can be moved back to pending."""
        self.review.action_approve()
        self.review.action_reset_to_pending()
        self.assertEqual(self.review.state, 'pending')

    def test_rating_constraint(self):
        """A rating outside 1-5 is refused by the database."""
        for rating in (0, 6):
            with self.subTest(rating=rating), self.assertRaises(IntegrityError), \
                    mute_logger('odoo.sql_db'), self.cr.savepoint():
                self.review.rating = rating
                self.review.flush_recordset()

    def test_server_actions(self):
        """The list server actions approve and reject the selected reviews."""
        approve = self.env.ref('theme_petzen.petzen_review_action_approve')
        reject = self.env.ref('theme_petzen.petzen_review_action_reject')
        approve.with_context(active_model='petzen.review', active_ids=self.review.ids).run()
        self.assertEqual(self.review.state, 'approved')
        reject.with_context(active_model='petzen.review', active_ids=self.review.ids).run()
        self.assertEqual(self.review.state, 'rejected')
