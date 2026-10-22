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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestTokenSession(TransactionCase):
    """Test suite for token.session model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TokenSession = cls.env['token.session']

    def test_token_session_create(self):
        """Test creating a token session generates reference number."""
        session = self.TokenSession.create({
            'name': 'Morning Session'
        })
        self.assertEqual(session.name, 'Morning Session')
        self.assertTrue(session.reference_no)
        self.assertEqual(session.opened_by, self.env.user)

    def test_token_session_create_custom_reference(self):
        """Test creating a token session with custom reference number."""
        session = self.TokenSession.create({
            'reference_no': 'CUSTOM-SES-001',
            'name': 'Afternoon Session'
        })
        self.assertEqual(session.reference_no, 'CUSTOM-SES-001')
