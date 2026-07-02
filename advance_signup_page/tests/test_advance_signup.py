# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
###############################################################################
from odoo.tests import HttpCase, tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSignupConfiguration(TransactionCase):

    def setUp(self):
        super().setUp()
        self.website = self.env['website'].search([], limit=1)
        self.config = self.env['signup.configuration'].create({
            'name': 'Test Signup Config',
            'website_id': self.website.id,
            'is_active': True,
            'signup_page_content': '<p>Welcome to Signup</p>',
            'login_page_content': '<p>Welcome to Login</p>',
            'reset_password_content': '<p>Reset your password</p>',
            'is_show_terms_conditions': True,
            'terms_and_conditions': '<p>Accept our terms.</p>',
        })

    def test_signup_configuration_creation(self):
        self.assertTrue(self.config.exists())
        self.assertEqual(self.config.name, 'Test Signup Config')
        self.assertEqual(self.config.website_id, self.website)
        self.assertTrue(self.config.is_active)

    def test_signup_page_content_fields(self):
        self.assertIn('Welcome to Signup', self.config.signup_page_content)
        self.assertIn('Welcome to Login', self.config.login_page_content)
        self.assertIn('Reset your password', self.config.reset_password_content)

    def test_terms_and_conditions_toggle(self):
        self.assertTrue(self.config.is_show_terms_conditions)
        self.assertIn('Accept our terms.', self.config.terms_and_conditions)
        self.config.write({'is_show_terms_conditions': False})
        self.assertFalse(self.config.is_show_terms_conditions)

    def test_unique_website_constraint(self):
        with self.assertRaises(Exception):
            with self.cr.savepoint():
                self.env['signup.configuration'].create({
                    'name': 'Duplicate Config',
                    'website_id': self.website.id,
                })
                self.env.flush_all()

    def test_signup_field_creation(self):
        user_fields = self.env['ir.model.fields'].search([
            ('model_id.model', '=', 'res.users'),
            ('ttype', '=', 'char'),
        ], limit=1)
        self.assertTrue(user_fields.exists())
        signup_field = self.env['signup.field'].create({
            'field_id': user_fields.id,
            'placeholder': 'Enter value',
            'help_description': 'This is a help text',
            'number_of_cols': '6',
            'is_required': True,
            'configuration_id': self.config.id,
        })
        self.assertTrue(signup_field.exists())
        self.assertEqual(signup_field.field_type, user_fields.ttype)
        self.assertEqual(signup_field.is_required, True)
        self.assertEqual(signup_field.placeholder, 'Enter value')

    def test_signup_field_linked_to_configuration(self):
        user_field = self.env['ir.model.fields'].search([
            ('model_id.model', '=', 'res.users'),
            ('ttype', '=', 'char'),
        ], limit=1)
        field = self.env['signup.field'].create({
            'field_id': user_field.id,
            'configuration_id': self.config.id,
            'number_of_cols': '12',
        })
        self.assertIn(field, self.config.signup_field_ids)

    def test_signup_field_type_auto_set_on_write(self):
        user_field_char = self.env['ir.model.fields'].search([
            ('model_id.model', '=', 'res.users'),
            ('ttype', '=', 'char'),
        ], limit=1)
        user_field_boolean = self.env['ir.model.fields'].search([
            ('model_id.model', '=', 'res.users'),
            ('ttype', '=', 'boolean'),
        ], limit=1)
        field = self.env['signup.field'].create({
            'field_id': user_field_char.id,
            'configuration_id': self.config.id,
            'number_of_cols': '6',
        })
        self.assertEqual(field.field_type, 'char')
        field.write({'field_id': user_field_boolean.id})
        self.assertEqual(field.field_type, 'boolean')

    def test_configuration_active_toggle(self):
        self.config.write({'is_active': False})
        self.assertFalse(self.config.is_active)
        self.config.write({'is_active': True})
        self.assertTrue(self.config.is_active)


@tagged('post_install', '-at_install')
class TestSignupPageHttp(HttpCase):

    def test_signup_page_returns_200(self):
        response = self.url_open('/web/signup')
        self.assertEqual(response.status_code, 200)

    def test_login_page_returns_200(self):
        response = self.url_open('/web/login')
        self.assertEqual(response.status_code, 200)
