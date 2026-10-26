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

from odoo.fields import Command
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPaymentProvider(TransactionCase):
    """Unit tests for the payment.provider model in customer_wise_payment_provider."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        # Create partners
        cls.partner_with_custom_provider = cls.env['res.partner'].create({
            'name': 'Customer With Custom Provider',
            'email': 'custom_provider_customer@test.com',
        })
        cls.partner_regular = cls.env['res.partner'].create({
            'name': 'Regular Customer',
            'email': 'regular_customer@test.com',
        })

        # Create test payment providers
        cls.public_provider = cls.env['payment.provider'].create({
            'name': 'Public Provider',
            'code': 'none',
            'is_published': True,
            'is_public': True,
            'company_id': cls.company.id,
        })
        cls.private_assigned_provider = cls.env['payment.provider'].create({
            'name': 'Private Assigned Provider',
            'code': 'none',
            'is_published': True,
            'is_public': False,
            'company_id': cls.company.id,
        })
        cls.private_unassigned_provider = cls.env['payment.provider'].create({
            'name': 'Private Unassigned Provider',
            'code': 'none',
            'is_published': True,
            'is_public': False,
            'company_id': cls.company.id,
        })

        # Assign private provider to partner
        cls.partner_with_custom_provider.write({
            'provider_ids': [Command.set([cls.private_assigned_provider.id])],
        })

    def test__find_available_providers(self):
        """Test _find_available_providers filtering based on is_public and partner provider_ids."""
        provider_model = self.env['payment.provider']

        # 1. Regular customer without special provider assignment:
        # Should see public provider, but not private providers
        available_regular = provider_model._find_available_providers(
            company_id=self.company.id,
            partner_id=self.partner_regular.id,
            amount=100.0,
        )
        self.assertIn(
            self.public_provider,
            available_regular,
            "Public provider should be available to regular customer",
        )
        self.assertNotIn(
            self.private_assigned_provider,
            available_regular,
            "Private assigned provider should NOT be available to regular customer",
        )
        self.assertNotIn(
            self.private_unassigned_provider,
            available_regular,
            "Private unassigned provider should NOT be available to regular customer",
        )

        # 2. Customer with assigned private provider:
        # Should see public provider AND assigned private provider, but not unassigned private provider
        available_custom = provider_model._find_available_providers(
            company_id=self.company.id,
            partner_id=self.partner_with_custom_provider.id,
            amount=100.0,
        )
        self.assertIn(
            self.public_provider,
            available_custom,
            "Public provider should be available to customer with custom provider",
        )
        self.assertIn(
            self.private_assigned_provider,
            available_custom,
            "Assigned private provider should be available to customer",
        )
        self.assertNotIn(
            self.private_unassigned_provider,
            available_custom,
            "Unassigned private provider should NOT be available to customer",
        )

        # 3. Public visitor without partner_id:
        # Should only see public provider
        available_public = provider_model._find_available_providers(
            company_id=self.company.id,
            partner_id=False,
            amount=100.0,
        )
        self.assertIn(
            self.public_provider,
            available_public,
            "Public provider should be available to public visitor",
        )
        self.assertNotIn(
            self.private_assigned_provider,
            available_public,
            "Private provider should NOT be available to public visitor",
        )
        self.assertNotIn(
            self.private_unassigned_provider,
            available_public,
            "Private unassigned provider should NOT be available to public visitor",
        )

        # 4. Dynamically assign private provider to regular customer and verify visibility
        self.partner_regular.write({
            'provider_ids': [Command.link(self.private_unassigned_provider.id)],
        })
        available_after_link = provider_model._find_available_providers(
            company_id=self.company.id,
            partner_id=self.partner_regular.id,
            amount=100.0,
        )
        self.assertIn(
            self.private_unassigned_provider,
            available_after_link,
            "Private provider should become available once linked to customer",
        )

    def test_find_available_providers(self):
        """Alias for test__find_available_providers to support standard naming conventions."""
        self.test__find_available_providers()
