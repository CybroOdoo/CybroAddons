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
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestCustomerGroup(TransactionCase):
    """Test cases for customer.group model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.CustomerGroup = cls.env['customer.group']
        cls.Partner = cls.env['res.partner']
        cls.Pricelist = cls.env['product.pricelist']

        # Setup test partners
        cls.partner_1 = cls.Partner.create({
            'name': 'Test Customer 1',
            'email': 'customer1@test.com',
        })
        cls.partner_2 = cls.Partner.create({
            'name': 'Test Customer 2',
            'email': 'customer2@test.com',
        })
        cls.partner_3 = cls.Partner.create({
            'name': 'Test Customer 3',
            'email': 'customer3@test.com',
        })

        # Setup test pricelist
        cls.pricelist_retail = cls.Pricelist.create({
            'name': 'Retail Pricelist',
        })
        cls.pricelist_wholesale = cls.Pricelist.create({
            'name': 'Wholesale Pricelist',
        })

    def test_01_create_customer_group(self):
        """Test creating a customer group with contacts and pricelist."""
        group = self.CustomerGroup.create({
            'name': 'VIP Retail Group',
            'contact_ids': [Command.set([self.partner_1.id, self.partner_2.id])],
            'pricelist_id': self.pricelist_retail.id,
        })

        self.assertEqual(group.name, 'VIP Retail Group')
        self.assertEqual(group.pricelist_id, self.pricelist_retail)
        self.assertEqual(len(group.contact_ids), 2)
        self.assertIn(self.partner_1, group.contact_ids)
        self.assertIn(self.partner_2, group.contact_ids)

    def test_02_update_customer_group(self):
        """Test updating fields and contacts on a customer group."""
        group = self.CustomerGroup.create({
            'name': 'Initial Group',
            'contact_ids': [Command.link(self.partner_1.id)],
            'pricelist_id': self.pricelist_retail.id,
        })

        # Update name and pricelist
        group.write({
            'name': 'Updated Group',
            'pricelist_id': self.pricelist_wholesale.id,
            'contact_ids': [Command.link(self.partner_2.id)],
        })

        self.assertEqual(group.name, 'Updated Group')
        self.assertEqual(group.pricelist_id, self.pricelist_wholesale)
        self.assertIn(self.partner_1, group.contact_ids)
        self.assertIn(self.partner_2, group.contact_ids)

        # Remove partner_1 using unlink command
        group.write({
            'contact_ids': [Command.unlink(self.partner_1.id)],
        })
        self.assertNotIn(self.partner_1, group.contact_ids)
        self.assertIn(self.partner_2, group.contact_ids)

    def test_03_customer_group_optional_fields(self):
        """Test creating customer group without contacts and pricelist."""
        group = self.CustomerGroup.create({
            'name': 'Empty Group',
        })

        self.assertEqual(group.name, 'Empty Group')
        self.assertFalse(group.contact_ids)
        self.assertFalse(group.pricelist_id)

    def test_04_multiple_contacts_in_group(self):
        """Test assigning multiple contacts at once."""
        group = self.CustomerGroup.create({
            'name': 'Multi Contacts Group',
            'contact_ids': [Command.set([self.partner_1.id, self.partner_2.id, self.partner_3.id])],
            'pricelist_id': self.pricelist_wholesale.id,
        })

        self.assertEqual(len(group.contact_ids), 3)
        self.assertEqual(set(group.contact_ids.ids), {self.partner_1.id, self.partner_2.id, self.partner_3.id})

    def test_05_unlink_customer_group(self):
        """Test unlinking a customer group retains contacts and pricelist."""
        group = self.CustomerGroup.create({
            'name': 'Temporary Group',
            'contact_ids': [Command.set([self.partner_1.id])],
            'pricelist_id': self.pricelist_retail.id,
        })
        group_id = group.id

        group.unlink()

        # Group should be deleted
        self.assertFalse(self.CustomerGroup.search([('id', '=', group_id)]))
        # Linked partner and pricelist should remain intact
        self.assertTrue(self.partner_1.exists())
        self.assertTrue(self.pricelist_retail.exists())

    def test_06_search_customer_group(self):
        """Test searching customer group by contact or pricelist."""
        group = self.CustomerGroup.create({
            'name': 'Searchable Group',
            'contact_ids': [Command.set([self.partner_3.id])],
            'pricelist_id': self.pricelist_wholesale.id,
        })

        found_by_partner = self.CustomerGroup.search([('contact_ids', 'in', self.partner_3.id)])
        self.assertIn(group, found_by_partner)

        found_by_pricelist = self.CustomerGroup.search([('pricelist_id', '=', self.pricelist_wholesale.id)])
        self.assertIn(group, found_by_pricelist)

    def test_07_access_rights(self):
        """Test standard internal user access rights on customer.group."""
        internal_user = self.env['res.users'].create({
            'name': 'Internal Test User',
            'login': 'internal_test_user@test.com',
            'email': 'internal_test_user@test.com',
            'group_ids': [Command.set([self.env.ref('base.group_user').id])],
        })

        group = self.CustomerGroup.with_user(internal_user).create({
            'name': 'User Created Group',
            'contact_ids': [Command.set([self.partner_1.id])],
            'pricelist_id': self.pricelist_retail.id,
        })
        self.assertEqual(group.name, 'User Created Group')
        read_group = self.CustomerGroup.with_user(internal_user).search([('id', '=', group.id)])
        self.assertEqual(read_group.id, group.id)

    def test_08_views_definition(self):
        """Test that list view loads correctly without architecture errors."""
        tree_view = self.env['customer.group'].get_view(
            view_id=self.env.ref('customer_group_pricelist.customer_group_view_tree').id,
            view_type='list'
        )
        self.assertTrue(tree_view['arch'])


