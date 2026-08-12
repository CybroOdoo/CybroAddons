# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from datetime import date
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestTokenToken(TransactionCase):
    """Test suite for token.token model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TokenToken = cls.env['token.token']
        cls.Department = cls.env['department']
        cls.QueueCounter = cls.env['queue.counter']

        cls.dept = cls.Department.create({
            'name': 'Support',
            'code': 'SUP'
        })
        cls.counter = cls.QueueCounter.create({
            'name': 'Counter 1'
        })

    def test_token_creation_and_defaults(self):
        """Test token creation, sequence generation, and default values."""
        token = self.TokenToken.create({
            'customer_name': 'Jane Doe',
            'department_id': self.dept.id,
            'mobile': '+1234567890'
        })
        self.assertTrue(token.reference_no)
        self.assertTrue(token.token)
        self.assertEqual(token.state, 'draft')

    def test_mobile_validation_valid(self):
        """Test valid mobile formats pass constraint."""
        valid_mobiles = [
            '+1234567890',
            '1234567890',
            '(123) 456-7890',
            '+91 9876543210'
        ]
        for mob in valid_mobiles:
            token = self.TokenToken.create({
                'customer_name': 'Test User',
                'department_id': self.dept.id,
                'mobile': mob
            })
            self.assertEqual(token.mobile, mob)

    def test_mobile_validation_invalid(self):
        """Test invalid mobile format raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.TokenToken.create({
                'customer_name': 'Invalid Mobile User',
                'department_id': self.dept.id,
                'mobile': '123-abc-456'
            })

    def test_get_report_base_filename(self):
        """Test filename generation for token report."""
        token = self.TokenToken.create({
            'customer_name': 'Test User',
            'department_id': self.dept.id,
            'mobile': '12345678'
        })
        expected_name = f"Token - {token.reference_no}"
        self.assertEqual(token._get_report_base_filename(), expected_name)

    def test_get_tokens_stats(self):
        """Test get_tokens stats calculation."""
        self.TokenToken.create({
            'customer_name': 'User 1',
            'department_id': self.dept.id,
            'mobile': '12345678',
            'state': 'draft'
        })
        self.TokenToken.create({
            'customer_name': 'User 2',
            'department_id': self.dept.id,
            'mobile': '12345678',
            'state': 'done'
        })
        stats = self.TokenToken.get_tokens(
            from_date=date.today(),
            to_date=date.today()
        )
        self.assertGreaterEqual(stats['total_queue_count'], 2)
        self.assertGreaterEqual(stats['total_queue_served'], 1)
        self.assertGreaterEqual(stats['total_queue_left'], 1)

    def test_pie_function(self):
        """Test pie_function method for chart visualization data."""
        self.TokenToken.create({
            'customer_name': 'Pie User',
            'department_id': self.dept.id,
            'mobile': '12345678',
            'state': 'draft'
        })
        pie_data = self.TokenToken.pie_function(
            from_date=date.today(),
            to_date=date.today()
        )
        self.assertIn('name', pie_data)
        self.assertIn('count', pie_data)

        pie_data_all = self.TokenToken.pie_function()
        self.assertIn('name', pie_data_all)
        self.assertIn('count', pie_data_all)

    def test_get_table_data(self):
        """Test get_table_data method for department aggregation."""
        self.TokenToken.create({
            'customer_name': 'Table User',
            'department_id': self.dept.id,
            'mobile': '12345678',
            'state': 'done'
        })
        table_data = self.TokenToken.get_table_data(
            from_date=date.today(),
            to_date=date.today()
        )
        self.assertTrue(isinstance(table_data, list))

        table_data_all = self.TokenToken.get_table_data()
        self.assertTrue(isinstance(table_data_all, list))
