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

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestTicketHelpdesk(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ticket_model = cls.env['ticket.helpdesk']
        cls.api = cls.env['zendesk.api']
        cls.api_cls = type(cls.api)

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'customer@example.com',
        })

    def setUp(self):
        super().setUp()
        self.api._set_param('is_connect_zendesk', 'True')
        self.ticket = self.ticket_model.create({
            'subject': 'Help with printer',
            'email': 'customer@example.com',
            'customer_id': self.partner.id,
            'description': 'Printer is jammed',
            'priority': '2',
        })

    def test_actions_when_zendesk_disabled(self):
        self.api._set_param('is_connect_zendesk', 'False')
        res_create = self.ticket.action_create_to_zendesk()
        self.assertEqual(res_create['params']['type'], 'warning')
        self.assertIn("Zendesk connection is disabled", res_create['params']['message'])

        res_update = self.ticket.action_update_zendesk_ticket()
        self.assertEqual(res_update['params']['type'], 'warning')
        self.assertIn("Zendesk connection is disabled", res_update['params']['message'])

        res_delete = self.ticket.action_delete_zendesk_ticket()
        self.assertEqual(res_delete['params']['type'], 'warning')
        self.assertIn("Zendesk connection is disabled", res_delete['params']['message'])

    def test_prepare_zendesk_ticket_vals_with_and_without_description(self):
        vals = self.ticket._prepare_zendesk_ticket_vals(requester_id=555)
        self.assertEqual(vals['subject'], 'Help with printer')
        self.assertEqual(vals['priority'], 'normal')
        self.assertEqual(vals['requester_id'], 555)
        self.assertEqual(vals['comment'], {'body': 'Printer is jammed'})

        # Without description and priority 0 using in-memory record
        new_ticket = self.ticket_model.new({
            'subject': 'No Desc Ticket',
            'email': 'customer@example.com',
            'customer_id': self.partner.id,
            'description': False,
            'priority': '0',
        })
        vals_no_desc = new_ticket._prepare_zendesk_ticket_vals(requester_id=555)
        self.assertIsNone(vals_no_desc['priority'])
        self.assertNotIn('comment', vals_no_desc)

    def test_action_create_to_zendesk_already_exists(self):
        self.ticket.zendesk_ticket_no = '12345'
        res = self.ticket.action_create_to_zendesk()
        self.assertEqual(res['params']['type'], 'warning')
        self.assertEqual(res['params']['message'], 'Ticket already exists')

    def test_action_create_to_zendesk_failure(self):
        with patch.object(self.api_cls, '_find_or_create_user', side_effect=UserError('Zendesk API error')):
            res = self.ticket.action_create_to_zendesk()
            self.assertEqual(res['params']['type'], 'danger')
            self.assertIn('Creation of Zendesk ticket failed', res['params']['message'])
            self.assertFalse(self.ticket.zendesk_ticket_no)

    def test_action_create_to_zendesk_success(self):
        with patch.object(self.api_cls, '_find_or_create_user', return_value=999) as mock_user, \
             patch.object(self.api_cls, '_request', return_value={'ticket': {'id': 78901}}) as mock_req:
            res = self.ticket.action_create_to_zendesk()
            mock_user.assert_called_once_with('Test Customer', 'customer@example.com')
            mock_req.assert_called_once()
            self.assertEqual(self.ticket.zendesk_ticket_no, '78901')
            self.assertEqual(res['params']['type'], 'success')
            self.assertIn('Successfully Created', res['params']['message'])

    def test_action_update_zendesk_ticket_unlinked(self):
        self.ticket.zendesk_ticket_no = False
        res = self.ticket.action_update_zendesk_ticket()
        self.assertEqual(res['params']['type'], 'warning')
        self.assertIn('not linked to Zendesk yet', res['params']['message'])

    def test_action_update_zendesk_ticket_failure(self):
        self.ticket.zendesk_ticket_no = '78901'
        with patch.object(self.api_cls, '_find_or_create_user', return_value=999), \
             patch.object(self.api_cls, '_request', side_effect=UserError('Failed to put')):
            res = self.ticket.action_update_zendesk_ticket()
            self.assertEqual(res['params']['type'], 'danger')
            self.assertIn('Updating the ticket failed', res['params']['message'])

    def test_action_update_zendesk_ticket_success(self):
        self.ticket.zendesk_ticket_no = '78901'
        with patch.object(self.api_cls, '_find_or_create_user', return_value=999), \
             patch.object(self.api_cls, '_request', return_value={'ticket': {'id': 78901}}) as mock_req:
            res = self.ticket.action_update_zendesk_ticket()
            mock_req.assert_called_once()
            self.assertEqual(res['params']['type'], 'success')
            self.assertEqual(res['params']['message'], 'Successfully Updated the ticket')

    def test_action_delete_zendesk_ticket_unlinked(self):
        self.ticket.zendesk_ticket_no = False
        res = self.ticket.action_delete_zendesk_ticket()
        self.assertEqual(res['params']['type'], 'warning')
        self.assertIn('not linked to Zendesk', res['params']['message'])

    def test_action_delete_zendesk_ticket_success_204_and_404(self):
        self.ticket.write({'zendesk_ticket_no': '78901', 'is_ticket_from_zendesk': True})
        mock_resp_204 = MagicMock(status_code=204)
        with patch.object(self.api_cls, '_raw_request', return_value=mock_resp_204) as mock_raw:
            res = self.ticket.action_delete_zendesk_ticket()
            mock_raw.assert_called_once_with('DELETE', 'tickets/78901.json', timeout=180)
            self.assertEqual(res['params']['type'], 'success')
            self.assertFalse(self.ticket.zendesk_ticket_no)
            self.assertFalse(self.ticket.is_ticket_from_zendesk)

        # 404 Not Found (already deleted in Zendesk)
        self.ticket.write({'zendesk_ticket_no': '78902', 'is_ticket_from_zendesk': True})
        mock_resp_404 = MagicMock(status_code=404)
        with patch.object(self.api_cls, '_raw_request', return_value=mock_resp_404):
            res = self.ticket.action_delete_zendesk_ticket()
            self.assertEqual(res['params']['type'], 'success')
            self.assertFalse(self.ticket.zendesk_ticket_no)

    def test_action_delete_zendesk_ticket_failure_500(self):
        self.ticket.write({'zendesk_ticket_no': '78901'})
        mock_resp_500 = MagicMock(status_code=500, text='Internal Server Error')
        with patch.object(self.api_cls, '_raw_request', return_value=mock_resp_500):
            res = self.ticket.action_delete_zendesk_ticket()
            self.assertEqual(res['params']['type'], 'danger')
            self.assertIn('Have issues with deleting the ticket', res['params']['message'])
            self.assertEqual(self.ticket.zendesk_ticket_no, '78901')
