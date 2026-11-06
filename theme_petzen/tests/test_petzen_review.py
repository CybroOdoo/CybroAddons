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


@tagged('post_install', '-at_install', 'petzen_review')
class TestPetzenReview(TransactionCase):

    def _review(self, **kw):
        vals = {'name': 'Anu', 'email': 'anu@example.com',
                'review': 'Great service!'}
        vals.update(kw)
        return self.env['petzen.review'].create(vals)

    def test_defaults(self):
        review = self._review()
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.customer_type, 'verified')
        self.assertEqual(review.state, 'pending')

    def test_rating_must_be_between_1_and_5(self):
        for rating in (1, 5):
            self.assertEqual(self._review(rating=rating).rating, rating)
        for rating in (0, 6):
            with self.assertRaises(IntegrityError), \
                    mute_logger('odoo.sql_db'), self.cr.savepoint():
                self._review(rating=rating)
                self.env['petzen.review'].flush_model()

    def test_workflow_actions(self):
        review = self._review()
        review.action_approve()
        self.assertEqual(review.state, 'approved')
        review.action_reject()
        self.assertEqual(review.state, 'rejected')
        review.action_reset_to_pending()
        self.assertEqual(review.state, 'pending')

    def test_actions_on_multiple_records(self):
        reviews = self._review() | self._review()
        reviews.action_approve()
        self.assertEqual(set(reviews.mapped('state')), {'approved'})