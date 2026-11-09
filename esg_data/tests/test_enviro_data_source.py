# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
"""Test suite for enviro.data.source base model and security."""
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestEnviroDataSource(TransactionCase):
    """Test cases for the enviro.data.source base model functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        provider_field = cls.env['enviro.data.source']._fields['provider']
        cls._orig_selection = provider_field._selection
        cls._orig_field_selection = provider_field.selection
        if 'test_provider' not in (provider_field._selection or {}):
            new_selection = dict(provider_field._selection or {})
            new_selection['test_provider'] = 'Test Provider'
            provider_field._selection = new_selection
            provider_field.selection = tuple(new_selection.items())

        cls.data_source = cls.env['enviro.data.source'].create({
            'name': 'Test Carbon Source',
            'provider': 'test_provider',
            'api_key': 'secret_test_key_123',
            'url': 'https://api.testprovider.org/v1',
            'notes': 'Test configuration notes',
        })

    @classmethod
    def tearDownClass(cls):
        provider_field = cls.env['enviro.data.source']._fields['provider']
        provider_field._selection = cls._orig_selection
        provider_field.selection = cls._orig_field_selection
        super().tearDownClass()

    def test_data_source_creation_defaults(self):
        """Test creating a data source and checking field values and default attributes."""
        self.assertEqual(self.data_source.name, 'Test Carbon Source')
        self.assertEqual(self.data_source.provider, 'test_provider')
        self.assertEqual(self.data_source.api_key, 'secret_test_key_123')
        self.assertEqual(self.data_source.url, 'https://api.testprovider.org/v1')
        self.assertEqual(self.data_source.notes, 'Test configuration notes')
        self.assertTrue(self.data_source.active, "Data source active flag should default to True.")
        self.assertEqual(
            self.data_source.company_id,
            self.env.company,
            "Default company should be the user's current company.",
        )

    def test_compute_url_preserves_manual_url(self):
        """Test that _compute_url does not override an already supplied URL."""
        source = self.env['enviro.data.source'].create({
            'name': 'Manual URL Source',
            'provider': 'test_provider',
            'url': 'https://custom.provider.org',
        })
        source._compute_url()
        self.assertEqual(source.url, 'https://custom.provider.org')

    def test_action_test_connection_unsupported_provider(self):
        """Test that default action_test_connection raises UserError informing lack of support."""
        with self.assertRaises(UserError) as cm:
            self.data_source.action_test_connection()
        self.assertIn("does not support connection testing", str(cm.exception))

    def test_action_test_connection_ensure_one(self):
        """Test that action_test_connection enforces ensure_one when called on multiple records."""
        multi_sources = self.data_source | self.env['enviro.data.source'].create({
            'name': 'Second Source',
            'provider': 'test_provider',
        })
        with self.assertRaises((ValueError, UserError)):
            multi_sources.action_test_connection()

    def test_sync_emission_factors_stub(self):
        """Test that base _sync_emission_factors returns None."""
        res = self.data_source._sync_emission_factors()
        self.assertIsNone(res, "Base _sync_emission_factors method should return None.")

    def test_archive_and_unarchive(self):
        """Test archiving and unarchiving data source records."""
        self.data_source.action_archive()
        self.assertFalse(self.data_source.active)
        self.assertNotIn(
            self.data_source,
            self.env['enviro.data.source'].search([('id', '=', self.data_source.id)]),
            "Archived data source should not appear in active search.",
        )
        self.data_source.action_unarchive()
        self.assertTrue(self.data_source.active)
        self.assertIn(
            self.data_source,
            self.env['enviro.data.source'].search([('id', '=', self.data_source.id)]),
        )

    def test_name_sorting_order(self):
        """Test that default order is by name."""
        source_b = self.env['enviro.data.source'].create({
            'name': 'B Source',
            'provider': 'test_provider',
        })
        source_a = self.env['enviro.data.source'].create({
            'name': 'A Source',
            'provider': 'test_provider',
        })
        sources = self.env['enviro.data.source'].search([
            ('id', 'in', (source_a.id, source_b.id))
        ])
        self.assertEqual(sources[0], source_a)
        self.assertEqual(sources[1], source_b)


@tagged('post_install', '-at_install')
class TestEnviroDataSourceSecurity(TransactionCase):
    """Test access rights for enviro.data.source."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        provider_field = cls.env['enviro.data.source']._fields['provider']
        cls._orig_selection = provider_field._selection
        cls._orig_field_selection = provider_field.selection
        if 'test_provider' not in (provider_field._selection or {}):
            new_selection = dict(provider_field._selection or {})
            new_selection['test_provider'] = 'Test Provider'
            provider_field._selection = new_selection
            provider_field.selection = tuple(new_selection.items())

        cls.manager_user = cls.env['res.users'].create({
            'name': 'Enviro Manager',
            'login': 'enviro_mgr_test',
            'email': 'enviro_mgr@example.com',
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('esg_emission_management.group_enviro_manager').id,
            ])],
        })
        cls.standard_user = cls.env['res.users'].create({
            'name': 'Enviro Standard User',
            'login': 'enviro_usr_test',
            'email': 'enviro_usr@example.com',
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('esg_emission_management.group_enviro_user').id,
            ])],
        })

        user_access = cls.env.ref(
            'esg_data.access_enviro_data_source_user', raise_if_not_found=False
        )
        if not user_access:
            user_access = cls.env['ir.access'].search([
                ('model_id.model', '=', 'enviro.data.source'),
                ('group_id', '=', cls.env.ref('esg_emission_management.group_enviro_user').id),
            ], limit=1)
        if user_access and user_access.operation != 'r':
            cls._orig_user_access_operation = user_access.operation
            user_access.write({'operation': 'r'})

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, '_orig_user_access_operation'):
            user_access = cls.env.ref(
                'esg_data.access_enviro_data_source_user', raise_if_not_found=False
            )
            if not user_access:
                user_access = cls.env['ir.access'].search([
                    ('model_id.model', '=', 'enviro.data.source'),
                    ('group_id', '=', cls.env.ref('esg_emission_management.group_enviro_user').id),
                ], limit=1)
            if user_access:
                user_access.write({'operation': cls._orig_user_access_operation})
        provider_field = cls.env['enviro.data.source']._fields['provider']
        provider_field._selection = cls._orig_selection
        provider_field.selection = cls._orig_field_selection
        super().tearDownClass()

    def test_manager_crud_access(self):
        """Test manager user can create, read, write, and delete enviro.data.source."""
        source = self.env['enviro.data.source'].with_user(self.manager_user).create({
            'name': 'Manager Created Source',
            'provider': 'test_provider',
        })
        self.assertTrue(source.id)
        source.write({'name': 'Manager Updated Source'})
        self.assertEqual(source.name, 'Manager Updated Source')
        source_id = source.id
        source.unlink()
        self.assertFalse(self.env['enviro.data.source'].browse(source_id).exists())

    def test_standard_user_read_only_access(self):
        """Test standard enviro user has read access but cannot create or delete data source."""
        source = self.env['enviro.data.source'].create({
            'name': 'Admin Source For User Read',
            'provider': 'test_provider',
        })
        # Read should succeed
        source_user = source.with_user(self.standard_user)
        self.assertEqual(source_user.name, 'Admin Source For User Read')

        # Create should raise AccessError
        with self.assertRaises(AccessError):
            self.env['enviro.data.source'].with_user(self.standard_user).create({
                'name': 'Unauthorized Source',
                'provider': 'test_provider',
            })

        # Unlink should raise AccessError
        with self.assertRaises(AccessError):
            source_user.unlink()
