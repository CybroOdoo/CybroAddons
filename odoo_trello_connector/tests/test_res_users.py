# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class MockResponse:
    """Helper mock class for requests.get/post/put responses"""

    def __init__(self, json_data, status_code=200, text=''):
        self._json_data = json_data
        self.status_code = status_code
        self.text = text

    def json(self):
        return self._json_data


class TestResUsers(TransactionCase):
    """Test cases for res.users Trello API integration"""

    def setUp(self):
        super().setUp()
        self.user = self.env.user
        self.user.write({
            'api_key': 'test_api_key_001',
            'token': 'test_token_001',
            'user_name': 'test_trello_user',
        })
        self.headers = {'Accept': 'application/json'}
        self.query = {
            'key': self.user.api_key,
            'token': self.user.token,
        }

    def test_01_action_import_missing_credentials(self):
        """Test that action_import raises ValidationError if credentials missing"""
        self.user.write({'api_key': False, 'token': False, 'user_name': False})
        with self.assertRaises(ValidationError):
            self.user.action_import()

    def test_02_action_import_missing_api_key(self):
        """Test that action_import raises ValidationError if api_key missing"""
        self.user.write({'api_key': False})
        with self.assertRaises(ValidationError):
            self.user.action_import()

    def test_03_action_import_missing_token(self):
        """Test that action_import raises ValidationError if token missing"""
        self.user.write({'token': False})
        with self.assertRaises(ValidationError):
            self.user.action_import()

    def test_04_action_export_missing_credentials(self):
        """Test that action_export raises ValidationError if credentials missing"""
        self.user.write({'api_key': False, 'token': False, 'user_name': False})
        with self.assertRaises(ValidationError):
            self.user.action_export()

    @patch('odoo.addons.odoo_trello_connector.models.res_users.requests.get')
    def test_05_get_member_id_success(self, mock_get):
        """Test get_member_id returns correct member id on success"""
        mock_get.return_value = MockResponse({'id': 'member_abc123'}, 200)
        member_id = self.user.get_member_id(self.headers, 'test_trello_user')
        self.assertEqual(member_id, 'member_abc123')
        mock_get.assert_called_once()

    @patch('odoo.addons.odoo_trello_connector.models.res_users.requests.get')
    def test_06_get_member_id_not_found(self, mock_get):
        """Test get_member_id raises ValidationError on 404"""
        mock_get.return_value = MockResponse({}, 404, 'not found')
        with self.assertRaises(ValidationError):
            self.user.get_member_id(self.headers, 'bad_user')

    @patch('odoo.addons.odoo_trello_connector.models.res_users.requests.get')
    def test_07_get_member_id_server_error(self, mock_get):
        """Test get_member_id raises ValidationError on server error"""
        mock_get.return_value = MockResponse({}, 500, 'internal server error')
        with self.assertRaises(ValidationError):
            self.user.get_member_id(self.headers, 'test_trello_user')

    @patch('odoo.addons.odoo_trello_connector.models.res_users.requests.get')
    def test_08_get_boards_success(self, mock_get):
        """Test get_boards returns list of boards on success"""
        boards = [
            {'id': 'board1', 'name': 'Board One', 'desc': 'First board'},
            {'id': 'board2', 'name': 'Board Two', 'desc': 'Second board'},
        ]
        mock_get.return_value = MockResponse(boards, 200)
        result = self.user.get_boards(self.headers, self.query, 'member_abc123')
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['id'], 'board1')

    @patch('odoo.addons.odoo_trello_connector.models.res_users.requests.get')
    def test_09_get_boards_failure(self, mock_get):
        """Test get_boards raises ValidationError on failure"""
        mock_get.return_value = MockResponse({}, 401, 'unauthorized')
        with self.assertRaises(ValidationError):
            self.user.get_boards(self.headers, self.query, 'member_abc123')

    @patch('odoo.addons.odoo_trello_connector.models.res_users.requests.get')
    def test_10_get_cards_success(self, mock_get):
        """Test get_cards returns list of cards on success"""
        cards = [
            {'id': 'card1', 'name': 'Task One', 'idList': 'list1'},
            {'id': 'card2', 'name': 'Task Two', 'idList': 'list1'},
        ]
        mock_get.return_value = MockResponse(cards, 200)
        result = self.user.get_cards(self.headers, self.query, 'board1')
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['id'], 'card1')

    @patch('odoo.addons.odoo_trello_connector.models.res_users.requests.get')
    def test_11_get_cards_failure(self, mock_get):
        """Test get_cards raises ValidationError on failure"""
        mock_get.return_value = MockResponse({}, 403, 'forbidden')
        with self.assertRaises(ValidationError):
            self.user.get_cards(self.headers, self.query, 'board1')

    @patch('odoo.addons.odoo_trello_connector.models.res_users.requests.get')
    def test_12_get_list_on_board_success(self, mock_get):
        """Test get_list_on_board returns list of lists on success"""
        lists = [
            {'id': 'list1', 'name': 'To Do'},
            {'id': 'list2', 'name': 'In Progress'},
            {'id': 'list3', 'name': 'Done'},
        ]
        mock_get.return_value = MockResponse(lists, 200)
        result = self.user.get_list_on_board(self.headers, self.query, 'board1')
        self.assertEqual(len(result), 3)
        self.assertEqual(result[1]['name'], 'In Progress')

    @patch('odoo.addons.odoo_trello_connector.models.res_users.requests.get')
    def test_13_get_list_on_board_failure(self, mock_get):
        """Test get_list_on_board raises ValidationError on failure"""
        mock_get.return_value = MockResponse({}, 500, 'server error')
        with self.assertRaises(ValidationError):
            self.user.get_list_on_board(self.headers, self.query, 'board1')

    @patch('odoo.addons.odoo_trello_connector.models.res_users.requests.get')
    def test_14_get_a_list_success(self, mock_get):
        """Test get_a_list returns list detail on success"""
        list_data = {'id': 'list1', 'name': 'To Do'}
        mock_get.return_value = MockResponse(list_data, 200)
        result = self.user.get_a_list(self.headers, self.query, 'list1')
        self.assertEqual(result['id'], 'list1')
        self.assertEqual(result['name'], 'To Do')

    @patch('odoo.addons.odoo_trello_connector.models.res_users.requests.get')
    def test_15_get_a_list_failure(self, mock_get):
        """Test get_a_list raises ValidationError on failure"""
        mock_get.return_value = MockResponse({}, 401, 'unauthorized')
        with self.assertRaises(ValidationError):
            self.user.get_a_list(self.headers, self.query, 'list1')

    def test_16_trello_fields_on_user(self):
        """Test that Trello fields exist on res.users"""
        self.assertIn('api_key', self.env['res.users']._fields)
        self.assertIn('token', self.env['res.users']._fields)
        self.assertIn('user_name', self.env['res.users']._fields)

    def test_17_user_trello_credentials_set(self):
        """Test that trello credentials are set correctly"""
        self.assertEqual(self.user.api_key, 'test_api_key_001')
        self.assertEqual(self.user.token, 'test_token_001')
        self.assertEqual(self.user.user_name, 'test_trello_user')
