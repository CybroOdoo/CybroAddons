# -*- coding: utf-8 -*-
from unittest.mock import patch
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestMondayConnector(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestMondayConnector, cls).setUpClass()
        cls.credential = cls.env['monday.credential'].create({
            'name': 'Test Credential',
            'token': 'test_token',
        })
        cls.wizard = cls.env['monday.connector'].create({
            'credential_id': cls.credential.id,
            'import_user': True,
            'import_board': True,
            'import_group': True,
            'import_item': True,
            'import_contact': True,
        })

    @patch('odoo.addons.monday_odoo_connector.wizard.monday_connector.requests.post')
    def test_import_users_success(self, mock_post):
        """Test user import logic."""
        mock_response = mock_post.return_value
        mock_response.json.return_value = {
            'data': {
                'users': [
                    {'id': '123', 'name': 'Test User', 'email': 'test@example.com'}
                ]
            }
        }
        
        self.wizard.import_board = False
        self.wizard.action_execute()
        
        # Check if user is created
        user = self.env['res.users'].search([('login', '=', 'test@example.com')])
        self.assertTrue(user)
        self.assertEqual(user.name, 'Test User')
        self.assertEqual(user.monday_reference, '123')

    @patch('odoo.addons.monday_odoo_connector.wizard.monday_connector.requests.post')
    def test_import_boards_success(self, mock_post):
        """Test board, group, item and contact import logic."""
        mock_response = mock_post.return_value
        mock_response.json.return_value = {
            'data': {
                'boards': [
                    {
                        'id': 'b1',
                        'name': 'Test Board',
                        'owner': {'name': 'Owner Name'},
                        'groups': [
                            {'id': 'g1', 'title': 'Test Group'}
                        ],
                        'items_page': {
                            'items': [
                                {
                                    'name': 'Test Item',
                                    'column_values': [
                                        {'id': 'c1', 'text': 'Value 1'}
                                    ]
                                }
                            ]
                        }
                    },
                    {
                        'id': 'b2',
                        'name': 'Contacts',
                        'owner': {'name': 'Owner Name'},
                        'groups': [],
                        'items_page': {
                            'items': [
                                {
                                    'name': 'Test Contact',
                                    'column_values': [
                                        {'id': 'contact_email', 'text': 'contact@example.com'},
                                        {'id': 'contact_phone', 'text': '1234567890'},
                                        {'id': 'Company', 'text': 'Test Company'}
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }
        }
        
        self.wizard.import_user = False
        self.wizard.action_execute()
        
        # Check board creation
        board = self.env['monday.board'].search([('board_reference', '=', 'b1')])
        self.assertTrue(board)
        self.assertEqual(board.name, 'Test Board')
        self.assertEqual(board.owner, 'Owner Name')
        
        # Check group creation
        group = self.env['monday.group'].search([('group', '=', 'g1'), ('board_id', '=', board.id)])
        self.assertTrue(group)
        self.assertEqual(group.name, 'Test Group')
        
        # Check item creation
        item = self.env['monday.item'].search([('name', '=', 'Test Item'), ('board_id', '=', board.id)])
        self.assertTrue(item)
        
        # Check contact creation (from Contacts board)
        partner = self.env['res.partner'].search([('email', '=', 'contact@example.com')])
        self.assertTrue(partner)
        self.assertEqual(partner.name, 'Test Contact')
        self.assertEqual(partner.phone, '1234567890')
        self.assertEqual(partner.company_name, 'Test Company')
        self.assertTrue(partner.monday_reference)

    @patch('odoo.addons.monday_odoo_connector.wizard.monday_connector.requests.post')
    def test_import_api_errors(self, mock_post):
        """Test API error handling."""
        mock_response = mock_post.return_value
        mock_response.json.return_value = {
            'error_code': 'auth_error',
            'error_message': 'Invalid token'
        }
        
        with self.assertRaises(ValidationError) as e:
            self.wizard.get_users("url", {})
        self.assertIn('Invalid token', str(e.exception))

        mock_response.json.return_value = {
            'errors': [{'message': 'GraphQL error'}]
        }
        with self.assertRaises(ValidationError) as e:
            self.wizard.get_boards("url", {})
        self.assertIn('GraphQL error', str(e.exception))
