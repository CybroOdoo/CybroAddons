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
#############################################################################
from datetime import date
from unittest.mock import patch
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestTokenToken(TransactionCase):
    """Test suite for token.token model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TokenToken = cls.env['token.token']
        cls.Department = cls.env['queue.department']
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

    def test_token_create_custom_reference(self):
        """Test creating a token with custom reference_no."""
        token = self.TokenToken.create({
            'reference_no': 'CUSTOM-TOK-001',
            'customer_name': 'Custom Ref User',
            'department_id': self.dept.id,
            'mobile': '+1234567890'
        })
        self.assertEqual(token.reference_no, 'CUSTOM-TOK-001')

    def test_generate_token_method(self):
        """Test direct invocation of _generate_token."""
        token_str = self.TokenToken._generate_token()
        self.assertTrue(token_str)

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

    def test_mobile_validation_empty_allowed(self):
        """Test that omitting mobile number does not raise validation error."""
        token = self.TokenToken.create({
            'customer_name': 'No Phone User',
            'department_id': self.dept.id,
            'mobile': False
        })
        self.assertFalse(token.mobile)

    def test_mobile_validation_invalid(self):
        """Test invalid mobile format raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.TokenToken.create({
                'customer_name': 'Invalid Mobile User',
                'department_id': self.dept.id,
                'mobile': '123-abc-456'
            })

    def test_mobile_validation_too_short(self):
        """Test mobile numbers shorter than 7 characters raise ValidationError."""
        with self.assertRaises(ValidationError):
            self.TokenToken.create({
                'customer_name': 'Short Mobile User',
                'department_id': self.dept.id,
                'mobile': '12345'
            })

    def test_mobile_validation_too_long(self):
        """Test mobile numbers longer than 20 characters raise ValidationError."""
        with self.assertRaises(ValidationError):
            self.TokenToken.create({
                'customer_name': 'Long Mobile User',
                'department_id': self.dept.id,
                'mobile': '+12345678901234567890123'
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

    def test_get_tokens_defaults(self):
        """Test get_tokens without date parameters defaults to today."""
        stats = self.TokenToken.get_tokens()
        self.assertIn('total_queue_count', stats)
        self.assertIn('total_queue_served', stats)
        self.assertIn('total_queue_left', stats)

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

    def test_token_create_fallback_reference(self):
        """Test fallback when sequence next_by_code returns False."""
        with patch.object(type(self.env['ir.sequence']), 'next_by_code', return_value=False):
            token = self.TokenToken.create({
                'customer_name': 'Fallback User',
                'department_id': self.dept.id,
            })
            self.assertEqual(token.reference_no, 'New')

    def test_token_access_token_and_user(self):
        """Test access_token generation and user_id assignment."""
        token = self.TokenToken.create({
            'customer_name': 'Secure User',
            'department_id': self.dept.id,
        })
        self.assertTrue(token.access_token)
        self.assertEqual(len(token.access_token), 32)

        token.user_id = self.env.user
        self.assertEqual(token.user_id, self.env.user)

    def test_portal_and_public_access_denied_on_token(self):
        """Test that public and portal users cannot directly read token.token (ACL restriction)."""
        from odoo.exceptions import AccessError
        token = self.TokenToken.create({
            'customer_name': 'Confidential Customer',
            'department_id': self.dept.id,
            'mobile': '+1234567890',
        })
        public_user = self.env.ref('base.public_user')
        from odoo.tests.common import new_test_user
        portal_user = new_test_user(self.env, 'portal_acl_test', groups='base.group_portal')

        with self.assertRaises(AccessError):
            token.with_user(public_user).read(['customer_name', 'mobile'])

        with self.assertRaises(AccessError):
            token.with_user(portal_user).read(['customer_name', 'mobile'])

