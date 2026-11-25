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
"""Contact data consumed by the Viber systray."""

from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged('post_install', '-at_install')
class TestViberUsers(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Users = cls.env['res.users'].with_context(active_test=True)
        cls.contact = new_test_user(
            cls.env, login='viber_contact', name='Viber Contact',
            groups='base.group_user', phone='+91 (987) 654-3210',
        )
        cls.no_phone = new_test_user(
            cls.env, login='viber_no_phone', name='Contact without phone',
            groups='base.group_user', phone=False,
        )
        cls.portal = new_test_user(
            cls.env, login='viber_portal', name='Portal Contact',
            groups='base.group_portal', phone='+1 555 0100',
        )
        cls.archived = new_test_user(
            cls.env, login='viber_archived', name='Archived Contact',
            groups='base.group_user', active=False,
        )

    def test_contact_payload(self):
        """Return each active user once with exactly the public contact fields."""
        result = self.Users.get_users()
        self.assertEqual(set(result), {'users'})
        contacts = result['users']
        self.assertIsInstance(contacts, list)
        self.assertEqual(len(contacts), len({row['id'] for row in contacts}))
        self.assertEqual(
            {row['id'] for row in contacts}, set(self.Users.search([('share', '=', False)]).ids),
        )
        for row in contacts:
            self.assertEqual(set(row), {'id', 'name', 'phone'})
        self.assertIn({
            'id': self.contact.id, 'name': 'Viber Contact',
            'phone': '+91 (987) 654-3210',
        }, contacts)

    def test_portal_users_are_excluded(self):
        """Only internal users are offered as Viber contacts."""
        ids = [row['id'] for row in self.Users.get_users()['users']]
        self.assertNotIn(self.portal.id, ids)
        self.assertIn(self.contact.id, ids)

    def test_contact_without_phone(self):
        """Users without a phone remain available with a false phone value."""
        contacts = {row['id']: row for row in self.Users.get_users()['users']}
        self.assertIs(contacts[self.no_phone.id]['phone'], False)

    def test_archived_contacts(self):
        """Respect the standard active_test context for archived users."""
        self.assertNotIn(
            self.archived.id, [row['id'] for row in self.Users.get_users()['users']],
        )
        contacts = self.Users.with_context(active_test=False).get_users()['users']
        self.assertIn(self.archived.id, [row['id'] for row in contacts])

    def test_updated_partner_contact_details(self):
        """Read current partner details instead of stale contact values."""
        self.contact.partner_id.write({
            'name': 'Updated Viber Contact', 'phone': '+44 123-456',
        })
        contacts = {row['id']: row for row in self.Users.get_users()['users']}
        self.assertEqual(contacts[self.contact.id], {
            'id': self.contact.id, 'name': 'Updated Viber Contact',
            'phone': '+44 123-456',
        })

    def test_internal_user_can_fetch_contacts(self):
        """The backend RPC works with an ordinary internal user's rights."""
        contacts = self.Users.with_user(self.contact).get_users()['users']
        self.assertIn(self.no_phone.id, [row['id'] for row in contacts])

    def test_singleton_does_not_limit_contact_list(self):
        """Calling on a user record still supplies the complete contact list."""
        self.assertEqual(self.contact.get_users(), self.Users.get_users())
