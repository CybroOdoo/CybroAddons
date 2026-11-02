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

from unittest.mock import MagicMock, patch

import requests

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged

POST = ('odoo.addons.monday_odoo_connector.models.monday_credential'
        '.requests.post')


def _response(payload, status=200):
    response = MagicMock()
    response.status_code = status
    response.ok = status < 400
    response.json.return_value = payload
    return response


def _item(ref, name, group='g1', columns=None):
    return {'id': ref, 'name': name, 'group': {'id': group},
            'column_values': columns or []}


@tagged('post_install', '-at_install')
class TestMondayConnector(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.credential = cls.env['monday.credential'].create({
            'name': 'Test Credential',
            'token': 'test_token',
        })
        cls.wizard = cls.env['monday.connector'].create({
            'credential_id': cls.credential.id,
            'import_board': True,
            'import_contact': True,
        })

    def _board(self, ref, name, columns=None, groups=None):
        return {'id': ref, 'name': name, 'description': None,
                'owner': {'name': 'Owner Name'},
                'columns': columns or [], 'groups': groups or []}

    def _mock_api(self, boards=None, items=None, users=None, next_items=None):
        """Return a side effect answering the queries by their kind."""
        def side_effect(url, json, headers, timeout):
            query = json['query']
            variables = json.get('variables', {})
            self.assertEqual(url, 'https://api.monday.com/v2')
            self.assertIn('API-Version', headers)
            if 'next_items_page' in query:
                return _response({'data': {'next_items_page': next_items(
                    variables['cursor'])}})
            if 'items_page' in query:
                ref = variables['board_ids'][0]
                return _response({'data': {'boards': [
                    {'items_page': items[ref]}]}})
            if 'boards' in query:
                page = variables['page']
                return _response({'data': {'boards': boards(page)}})
            return _response({'data': {'users': users(variables['page'])}})
        return side_effect

    def test_import_users_without_password(self):
        """Users are created without password, as portal users."""
        users = [
            {'id': '123', 'name': 'Test User', 'email': 'test@example.com'},
            {'id': '124', 'name': 'No Mail', 'email': None},
        ]
        wizard = self.wizard
        wizard.write({'import_board': False, 'import_user': True})
        with patch(POST, side_effect=self._mock_api(
                users=lambda page: users if page == 1 else [])):
            action = wizard.action_execute()
        self.assertEqual(action['tag'], 'display_notification')
        user = self.env['res.users'].search(
            [('login', '=', 'test@example.com')])
        self.assertEqual(user.name, 'Test User')
        self.assertEqual(user.monday_reference, '123')
        self.assertFalse(user.password)
        self.assertTrue(user.share)
        self.assertFalse(self.env['res.users'].with_context(
            active_test=False).search([('monday_reference', '=', '124')]))

    def test_import_users_existing_inactive(self):
        """Archived users are found and not created twice."""
        user = self.env['res.users'].create({
            'name': 'Old', 'login': 'old@example.com', 'active': False})
        wizard = self.wizard
        wizard.write({'import_board': False, 'import_user': True})
        users = [{'id': '9', 'name': 'Old', 'email': 'old@example.com'}]
        with patch(POST, side_effect=self._mock_api(
                users=lambda page: users if page == 1 else [])):
            wizard.action_execute()
        self.assertEqual(self.env['res.users'].with_context(
            active_test=False).search_count(
                [('login', '=', 'old@example.com')]), 1)
        self.assertFalse(user.monday_reference)

    def test_import_boards(self):
        """Boards, groups, items and customers are imported and updated."""
        columns = [{'id': 'c1', 'title': 'Status', 'type': 'status'}]
        boards = [self._board(
            'b1', 'Test Board', columns,
            [{'id': 'g1', 'title': 'Test Group'}])]
        items = {'b1': {'cursor': None, 'items': [
            _item('i1', 'Test Item', columns=[
                {'id': 'c1', 'type': 'status', 'text': 'Done'}])]}}
        wizard = self.wizard
        with patch(POST, side_effect=self._mock_api(
                boards=lambda page: boards if page == 1 else [],
                items=items)):
            wizard.action_execute()
            # a second run updates instead of duplicating
            items['b1']['items'][0]['name'] = 'Renamed Item'
            boards[0]['groups'][0]['title'] = 'Renamed Group'
            wizard.action_execute()
        board = self.env['monday.board'].search(
            [('board_reference', '=', 'b1')])
        self.assertEqual(len(board), 1)
        self.assertEqual(board.owner, 'Owner Name')
        self.assertEqual(board.group_ids.name, 'Renamed Group')
        self.assertEqual(len(board.item_ids), 1)
        item = board.item_ids
        self.assertEqual(item.name, 'Renamed Item')
        self.assertEqual(item.item_reference, 'i1')
        self.assertEqual(item.group_id, board.group_ids)
        self.assertEqual(item.column_value_ids.title, 'Status')
        self.assertEqual(item.column_value_ids.text, 'Done')

    def test_import_boards_without_owner(self):
        """A board without owner does not break the import."""
        board = self._board('b9', 'Ownerless')
        board['owner'] = None
        items = {'b9': {'cursor': None, 'items': []}}
        with patch(POST, side_effect=self._mock_api(
                boards=lambda page: [board] if page == 1 else [],
                items=items)):
            self.wizard.action_execute()
        self.assertFalse(self.env['monday.board'].search(
            [('board_reference', '=', 'b9')]).owner)

    def test_import_pagination(self):
        """All the pages of boards and all the item cursors are followed."""
        first_page = [self._board('p%s' % i, 'Board %s' % i)
                      for i in range(50)]
        second_page = [self._board('p50', 'Board 50')]
        items = {ref: {'cursor': None, 'items': []}
                 for ref in [b['id'] for b in first_page + second_page]}
        items['p50'] = {'cursor': 'c1', 'items': [_item('a', 'A')]}
        pages = {'c1': {'cursor': 'c2', 'items': [_item('b', 'B')]},
                 'c2': {'cursor': None, 'items': [_item('c', 'C')]}}
        with patch(POST, side_effect=self._mock_api(
                boards=lambda page: {1: first_page, 2: second_page}.get(
                    page, []),
                items=items, next_items=lambda cursor: pages[cursor])):
            self.wizard.action_execute()
        self.assertEqual(
            self.env['monday.board'].search_count(
                [('board_reference', '=like', 'p%')]), 51)
        board = self.env['monday.board'].search(
            [('board_reference', '=', 'p50')])
        self.assertEqual(sorted(board.item_ids.mapped('name')),
                         ['A', 'B', 'C'])

    def test_import_contacts(self):
        """Customers are created once and items without email are handled."""
        columns = [{'id': 'mail', 'title': 'Email', 'type': 'email'},
                   {'id': 'tel', 'title': 'Phone', 'type': 'phone'}]
        boards = [self._board('b2', 'Contacts', columns)]
        items = {'b2': {'cursor': None, 'items': [
            _item('1', 'Test Contact', columns=[
                {'id': 'mail', 'type': 'email', 'text': 'c@example.com'},
                {'id': 'tel', 'type': 'phone', 'text': '1234567890'}]),
            _item('2', 'No Email Contact', columns=[
                {'id': 'mail', 'type': 'email', 'text': ''},
                {'id': 'tel', 'type': 'phone', 'text': ''}]),
        ]}}
        # An existing partner without email must not match the empty email
        self.env['res.partner'].create({'name': 'Other'})
        with patch(POST, side_effect=self._mock_api(
                boards=lambda page: boards if page == 1 else [],
                items=items)):
            self.wizard.action_execute()
            self.wizard.action_execute()
        partner = self.env['res.partner'].search(
            [('email', '=', 'c@example.com')])
        self.assertEqual(len(partner), 1)
        self.assertEqual(partner.phone, '1234567890')
        self.assertTrue(partner.monday_reference)
        no_email = self.env['res.partner'].search(
            [('name', '=', 'No Email Contact')])
        self.assertEqual(len(no_email), 1)
        self.assertFalse(no_email.email)
        self.assertFalse(no_email.phone)

    def test_nothing_selected(self):
        self.wizard.import_board = False
        with self.assertRaises(UserError):
            self.wizard.action_execute()

    def test_api_errors(self):
        """API, HTTP and JSON errors are converted to user errors."""
        credential = self.credential
        with patch(POST, return_value=_response(
                {'error_code': 'auth_error',
                 'error_message': 'Invalid token'})):
            with self.assertRaisesRegex(ValidationError, 'Invalid token'):
                credential._monday_request('query { me { id } }')
        with patch(POST, return_value=_response(
                {'errors': [{'message': 'GraphQL error'}]})):
            with self.assertRaisesRegex(ValidationError, 'GraphQL error'):
                credential._monday_request('query { me { id } }')
        bad_json = _response(None, 502)
        bad_json.json.side_effect = ValueError
        with patch(POST, return_value=bad_json):
            with self.assertRaisesRegex(UserError, '502'):
                credential._monday_request('query { me { id } }')
        with patch(POST, return_value=_response({'data': {}}, 500)):
            with self.assertRaisesRegex(UserError, '500'):
                credential._monday_request('query { me { id } }')
        with patch(POST, side_effect=requests.exceptions.ConnectionError(
                'down')):
            with self.assertRaisesRegex(UserError, 'down'):
                credential._monday_request('query { me { id } }')
