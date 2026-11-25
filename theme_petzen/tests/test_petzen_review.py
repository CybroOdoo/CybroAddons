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

from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestPetzenReview(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.review = cls.env['petzen.review'].create({
            'name': 'Test Customer',
            'email': 'test@example.com',
            'review': 'Great products!',
            'rating': 5,
        })

    def test_default_state_is_pending(self):
        self.assertEqual(self.review.state, 'pending')

    def test_action_approve(self):
        self.review.action_approve()
        self.assertEqual(self.review.state, 'approved')

    def test_action_reject(self):
        self.review.action_reject()
        self.assertEqual(self.review.state, 'rejected')

    def test_action_reset_to_pending(self):
        self.review.action_approve()
        self.review.action_reset_to_pending()
        self.assertEqual(self.review.state, 'pending')

    @mute_logger('odoo.sql_db')
    def test_rating_constraint(self):
        with self.assertRaises(Exception):
            with self.cr.savepoint():
                self.env['petzen.review'].create({
                    'name': 'Bad',
                    'email': 'bad@example.com',
                    'review': 'x',
                    'rating': 6,
                })
