# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################
from unittest.mock import Mock, patch
import psycopg2
from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import common, tagged
from odoo.addons.advance_signup_page.controllers.auth_signup import AuthSignupHome


@tagged('post_install', '-at_install')
class TestAdvanceSignup(common.TransactionCase):
    """Test suite for Advance Signup Page module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env['website'].search([], limit=1) or cls.env['website'].create({'name': 'Test Website'})
        cls.controller = AuthSignupHome()
        cls.field_email = cls.env['ir.model.fields'].search([
            ('model', '=', 'res.users'),
            ('name', '=', 'email'),
        ], limit=1)
        cls.field_signature = cls.env['ir.model.fields'].search([
            ('model', '=', 'res.users'),
            ('name', '=', 'signature'),
        ], limit=1)

    def test_01_signup_configuration_crud_and_constraint(self):
        """Test signup configuration creation and website unique constraint."""
        config = self.env['signup.configuration'].create({
            'name': 'Website 1 Signup Config',
            'website_id': self.website.id,
            'is_active': True,
            'signup_page_content': '<p>Welcome to signup</p>',
            'login_page_content': '<p>Welcome to login</p>',
            'reset_password_content': '<p>Reset your password</p>',
            'is_show_terms_conditions': True,
            'terms_and_conditions': '<p>Terms and conditions text</p>',
        })
        self.assertTrue(config.id)
        self.assertTrue(config.is_active)
        self.assertEqual(config.website_id, self.website)

        # Unique website constraint check
        with self.assertRaises(psycopg2.IntegrityError):
            with self.cr.savepoint():
                self.env['signup.configuration'].create({
                    'name': 'Duplicate Website Config',
                    'website_id': self.website.id,
                })

    def test_02_signup_field_creation_and_type_computation(self):
        """Test signup field creation, automatic type assignment, and write."""
        config = self.env['signup.configuration'].create({
            'name': 'Field Test Config',
            'website_id': self.env['website'].create({'name': 'Second Website'}).id,
        })
        signup_field = self.env['signup.field'].create({
            'configuration_id': config.id,
            'field_id': self.field_email.id,
            'placeholder': 'Enter your email',
            'number_of_cols': '6',
            'is_required': True,
        })
        self.assertEqual(signup_field.field_type, self.field_email.ttype)
        self.assertEqual(signup_field.name, self.field_email.field_description)

        # Test write function updating field_type
        if self.field_signature:
            signup_field.write({'field_id': self.field_signature.id})
            self.assertEqual(signup_field.field_type, self.field_signature.ttype)

        # Test write function clearing field_id
        signup_field.write({'field_id': False})
        self.assertFalse(signup_field.field_type)

        # Test creating field without field_id (record must be created and not dropped)
        field_without_id = self.env['signup.field'].create({
            'configuration_id': config.id,
            'placeholder': 'Custom placeholder',
        })
        self.assertTrue(field_without_id.id)
        self.assertFalse(field_without_id.field_type)

        # Test batch creation with and without field_id
        batch_fields = self.env['signup.field'].create([
            {'configuration_id': config.id, 'placeholder': 'Batch Field 1'},
            {'configuration_id': config.id, 'field_id': self.field_email.id},
        ])
        self.assertEqual(len(batch_fields), 2)
        self.assertFalse(batch_fields[0].field_type)
        self.assertEqual(batch_fields[1].field_type, self.field_email.ttype)

    def test_03_controller_get_signup_configuration(self):
        """Test controller _get_signup_configuration resolution."""
        new_website = self.env['website'].create({'name': 'Third Website'})
        config = self.env['signup.configuration'].create({
            'name': 'Third Website Config',
            'website_id': new_website.id,
        })

        mock_request = Mock()
        mock_request.env = self.env(context={'website_id': new_website.id})
        with patch('odoo.http.request', mock_request), \
             patch('odoo.addons.advance_signup_page.controllers.auth_signup.request', mock_request):
            found_config = self.controller._get_signup_configuration()
            self.assertEqual(found_config, config)

    def test_04_controller_prepare_signup_values(self):
        """Test _prepare_signup_values with dynamic fields and validations."""
        new_website = self.env['website'].create({'name': 'Fourth Website'})
        config = self.env['signup.configuration'].create({
            'name': 'Values Test Config',
            'website_id': new_website.id,
        })
        self.env['signup.field'].create({
            'configuration_id': config.id,
            'field_id': self.field_email.id,
        })

        mock_request = Mock()
        mock_request.env = self.env(context={'website_id': new_website.id, 'lang': 'en_US'})

        with patch('odoo.http.request', mock_request), \
             patch('odoo.addons.auth_signup.controllers.main.request', mock_request), \
             patch('odoo.addons.advance_signup_page.controllers.auth_signup.request', mock_request):
            # Normal valid signup
            qcontext = {
                'login': 'testuser@example.com',
                'name': 'Test User',
                'password': 'SecretPassword123',
                'confirm_password': 'SecretPassword123',
                'email': 'testuser@example.com',
            }
            values = self.controller._prepare_signup_values(qcontext)
            self.assertEqual(values['login'], 'testuser@example.com')
            self.assertEqual(values['name'], 'Test User')
            self.assertEqual(values['email'], 'testuser@example.com')
            self.assertIn('lang', values)

            # Password mismatch
            qcontext_mismatch = dict(qcontext, confirm_password='DifferentPassword')
            with self.assertRaises(UserError):
                self.controller._prepare_signup_values(qcontext_mismatch)

            # Invalid email validation
            with self.assertRaises(UserError):
                self.controller._prepare_signup_values(dict(qcontext, login='invalid-email'), validate_email=True)

    def test_05_views_and_actions(self):
        """Test action and menu references exist."""
        action = self.env.ref('advance_signup_page.signup_configuration_action')
        self.assertEqual(action.res_model, 'signup.configuration')
        menu = self.env.ref('advance_signup_page.signup_configuration_menu')
        self.assertEqual(menu.action, action)

    def test_06_acl_permissions(self):
        """Test that website designer has CRUD access and regular user without group cannot write."""
        designer_user = self.env['res.users'].create({
            'name': 'Website Designer User',
            'login': 'designer_user@example.com',
            'email': 'designer_user@example.com',
            'group_ids': [Command.set([
                self.env.ref('base.group_user').id,
                self.env.ref('website.group_website_designer').id,
            ])],
        })
        config = self.env['signup.configuration'].with_user(designer_user).create({
            'name': 'Designer Website Config',
            'website_id': self.env['website'].create({'name': 'Designer Website'}).id,
        })
        self.assertTrue(config.id)
        config.with_user(designer_user).write({'name': 'Updated Designer Config'})
        self.assertEqual(config.name, 'Updated Designer Config')

        # Regular user without website designer group should be restricted from creating configuration
        regular_user = self.env['res.users'].create({
            'name': 'Regular Internal User',
            'login': 'regular_user@example.com',
            'email': 'regular_user@example.com',
            'group_ids': [Command.set([self.env.ref('base.group_user').id])],
        })
        with self.assertRaises(AccessError):
            self.env['signup.configuration'].with_user(regular_user).create({
                'name': 'Unauthorized Config',
                'website_id': self.env['website'].create({'name': 'Unauthorized Website'}).id,
            })

