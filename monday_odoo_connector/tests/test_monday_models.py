# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from unittest.mock import patch

from psycopg2 import IntegrityError

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestMondayModels(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.board = cls.env['monday.board'].create({
            'name': 'Test Board',
            'board_reference': 'B001',
            'owner': 'Test Owner',
            'description': 'A board for testing'
        })
        cls.group = cls.env['monday.group'].create({
            'name': 'Test Group',
            'group': 'G001',
            'board_id': cls.board.id
        })
        cls.item = cls.env['monday.item'].create({
            'name': 'Test Item',
            'board_id': cls.board.id,
            'column_value_ids': [(0, 0, {
                'title': 'Test Column',
                'text': 'Test Text'
            })]
        })

    def test_board_creation(self):
        """Test board creation and fields"""
        self.assertEqual(self.board.name, 'Test Board')
        self.assertEqual(self.board.board_reference, 'B001')

    def test_group_creation(self):
        """Test group creation and relationship to board"""
        self.assertEqual(self.group.name, 'Test Group')
        self.assertEqual(self.group.board_id, self.board)
        self.assertIn(self.group, self.board.group_ids)

    def test_item_creation(self):
        """Test item creation and relationship to board and columns"""
        self.assertEqual(self.item.name, 'Test Item')
        self.assertEqual(self.item.board_id, self.board)
        self.assertIn(self.item, self.board.item_ids)
        self.assertEqual(len(self.item.column_value_ids), 1)
        self.assertEqual(self.item.column_value_ids[0].title, 'Test Column')
        self.assertEqual(self.item.column_value_ids[0].text, 'Test Text')

    def test_partner_monday_reference(self):
        """Test partner monday reference field"""
        partner = self.env['res.partner'].create({
            'name': 'Monday Partner',
            'monday_reference': True
        })
        self.assertTrue(partner.monday_reference)

    def test_user_monday_reference(self):
        """Test user monday reference field"""
        user = self.env['res.users'].create({
            'name': 'Monday User',
            'login': 'mondayuser',
            'monday_reference': 'U001'
        })
        self.assertEqual(user.monday_reference, 'U001')

    def test_credential_test_connection_success(self):
        """Test action_test_connection success"""
        credential = self.env['monday.credential'].create({
            'name': 'Valid Credential',
            'token': 'valid_token_123'
        })
        with patch('odoo.addons.monday_odoo_connector.models.monday_credential.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'data': {
                    'me': {
                        'id': '101',
                        'name': 'Admin User',
                        'email': 'admin@example.com'
                    }
                }
            }
            action = credential.action_test_connection()
            self.assertEqual(action.get('type'), 'ir.actions.client')
            self.assertEqual(action.get('tag'), 'display_notification')
            self.assertEqual(action.get('params', {}).get('type'), 'success')

    def test_board_reference_unique(self):
        """A board can be imported only once"""
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'):
            with self.env.cr.savepoint():
                self.env['monday.board'].create({
                    'name': 'Duplicate', 'board_reference': 'B001'})

    def test_credential_test_connection_missing_token(self):
        """Test action_test_connection with missing token"""
        credential = self.env['monday.credential'].create({
            'name': 'Empty Token Credential',
            'token': False
        })
        with self.assertRaises(UserError):
            credential.action_test_connection()

    def test_credential_test_connection_api_error(self):
        """Test action_test_connection with API error"""
        credential = self.env['monday.credential'].create({
            'name': 'Invalid Credential',
            'token': 'invalid_token'
        })
        with patch('odoo.addons.monday_odoo_connector.models.monday_credential.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'error_code': 'InvalidToken',
                'error_message': 'The token provided is invalid.'
            }
            with self.assertRaises(ValidationError):
                credential.action_test_connection()

    def test_imported_data_is_admin_only(self):
        """Internal users cannot read the imported Monday.com data."""
        user = self.env['res.users'].create({
            'name': 'Internal User',
            'login': 'monday_internal_user',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        for record in (self.board, self.group, self.item):
            with self.assertRaises(AccessError):
                record.with_user(user).check_access('read')
