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

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestImportExportTicket(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wizard_model = cls.env['import.export.ticket']
        cls.wizard_cls = type(cls.wizard_model)
        cls.ticket_model = cls.env['ticket.helpdesk']
        cls.ticket_cls = type(cls.ticket_model)
        cls.partner_model = cls.env['res.partner']
        cls.api = cls.env['zendesk.api']
        cls.api_cls = type(cls.api)

        cls.partner = cls.partner_model.create({
            'name': 'Alice Smith',
            'email': 'alice@example.com',
        })

    def setUp(self):
        super().setUp()
        self.api._set_param('is_connect_zendesk', 'True')

    def test_action_import_export_when_disabled(self):
        self.api._set_param('is_connect_zendesk', 'False')
        wizard = self.wizard_model.create({
            'start_date': date(2026, 11, 1),
            'end_date': date(2026, 11, 5),
        })
        res_import = wizard.action_import_tickets()
        self.assertEqual(res_import['params']['type'], 'warning')
        self.assertIn("Zendesk connection is disabled", res_import['params']['message'])

        res_export = wizard.action_export_tickets()
        self.assertEqual(res_export['params']['type'], 'warning')
        self.assertIn("Zendesk connection is disabled", res_export['params']['message'])

    def test_check_start_date_validation(self):
        # start_date > end_date
        with self.assertRaises(ValidationError) as cm:
            wizard = self.wizard_model.create({
                'start_date': date(2026, 11, 20),
                'end_date': date(2026, 11, 10),
            })
            wizard.check_start_date()
        self.assertIn("Please check the date", str(cm.exception))

        # Missing date
        with self.assertRaises(ValidationError):
            wizard = self.wizard_model.new({'start_date': False, 'end_date': date(2026, 11, 10)})
            wizard.check_start_date()

        # Valid dates
        valid_wizard = self.wizard_model.create({
            'start_date': date(2026, 11, 1),
            'end_date': date(2026, 11, 10),
        })
        valid_wizard.check_start_date()

    def test_fetch_zendesk_tickets_pagination(self):
        wizard = self.wizard_model.create({
            'start_date': date(2026, 11, 1),
            'end_date': date(2026, 11, 5),
        })
        page1 = {
            'results': [{'id': 101, 'subject': 'Ticket 1'}],
            'next_page': 'https://testdomain.zendesk.com/api/v2/search.json?page=2',
        }
        page2 = {
            'results': [{'id': 102, 'subject': 'Ticket 2'}],
            'next_page': None,
        }
        with patch.object(self.api_cls, '_request', side_effect=[page1, page2]) as mock_req:
            tickets = wizard._fetch_zendesk_tickets()
            self.assertEqual(len(tickets), 2)
            self.assertEqual(tickets[0]['id'], 101)
            self.assertEqual(tickets[1]['id'], 102)
            self.assertEqual(mock_req.call_count, 2)

    def test_get_or_create_partner(self):
        wizard = self.wizard_model.create({
            'start_date': date(2026, 11, 1),
            'end_date': date(2026, 11, 5),
        })
        user_cache = {}

        # 1. Requester not in cache and user exists in Zendesk -> creates new res.partner
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {
            'user': {'name': 'Bob Unique', 'email': 'bob.unique@example.com'},
        }
        with patch.object(self.api_cls, '_raw_request', return_value=mock_resp):
            partner, email = wizard._get_or_create_partner(888, user_cache)
            self.assertEqual(partner.name, 'Bob Unique')
            self.assertEqual(email, 'bob.unique@example.com')
            self.assertIn(888, user_cache)

        # 2. Requester in cache and res.partner already exists (using self.partner)
        user_cache[999] = {'name': 'Alice Smith', 'email': 'alice@example.com'}
        with patch.object(self.api_cls, '_raw_request') as mock_raw:
            partner, email = wizard._get_or_create_partner(999, user_cache)
            mock_raw.assert_not_called()
            self.assertEqual(partner.id, self.partner.id)
            self.assertEqual(email, 'alice@example.com')

        # 3. Requester API failure (not ok) -> creates distinct partner per requester
        mock_resp_fail = MagicMock(ok=False)
        with patch.object(self.api_cls, '_raw_request', return_value=mock_resp_fail):
            partner, email = wizard._get_or_create_partner(777, user_cache)
            self.assertEqual(partner.name, 'Zendesk User #777')
            self.assertEqual(email, 'zendesk_user_777@example.com')

            # Another unknown requester does not reuse the same partner
            partner2, email2 = wizard._get_or_create_partner(666, user_cache)
            self.assertNotEqual(partner.id, partner2.id)
            self.assertEqual(partner2.name, 'Zendesk User #666')
            self.assertEqual(email2, 'zendesk_user_666@example.com')

    def test_action_import_tickets_success_and_updates(self):
        wizard = self.wizard_model.create({
            'start_date': date(2026, 11, 1),
            'end_date': date(2026, 11, 5),
        })
        # Existing ticket with zendesk_ticket_no = '301'
        existing_record = self.ticket_model.create({
            'subject': 'Old Subject',
            'email': 'existing@example.com',
            'description': 'Old description',
            'customer_id': self.partner.id,
            'zendesk_ticket_no': '301',
        })

        tickets_data = [
            {'id': 301, 'subject': 'Updated Zendesk Subject', 'description': 'Updated desc', 'priority': 'normal', 'requester_id': 1},
            {'id': 302, 'subject': 'New Imported Ticket', 'description': 'Imported desc', 'priority': 'urgent', 'requester_id': 2},
        ]
        with patch.object(self.wizard_cls, '_fetch_zendesk_tickets', return_value=tickets_data), \
             patch.object(self.wizard_cls, '_get_or_create_partner', return_value=(self.partner, 'alice@example.com')):
            res = wizard.action_import_tickets()
            self.assertEqual(res['params']['type'], 'success')
            self.assertIn('1 ticket(s) imported', res['params']['message'])
            self.assertIn('1 ticket(s) updated', res['params']['message'])

            # Verify the updated existing ticket
            existing_record.invalidate_recordset()
            self.assertEqual(existing_record.subject, 'Updated Zendesk Subject')
            self.assertEqual(existing_record.description, 'Updated desc')

            # Verify the newly imported ticket in Odoo
            new_ticket = self.ticket_model.search([('zendesk_ticket_no', '=', '302')])
            self.assertTrue(new_ticket)
            self.assertEqual(new_ticket.subject, 'New Imported Ticket')
            self.assertEqual(new_ticket.priority, '4')  # 'urgent' maps to '4'
            self.assertTrue(new_ticket.is_ticket_from_zendesk)

        # Import when only new tickets are returned (updated_count == 0)
        with patch.object(self.wizard_cls, '_fetch_zendesk_tickets', return_value=[{'id': 303, 'subject': 'Brand New Ticket', 'requester_id': 3}]), \
             patch.object(self.wizard_cls, '_get_or_create_partner', return_value=(self.partner, 'alice@example.com')):
            res_new = wizard.action_import_tickets()
            self.assertEqual(res_new['params']['type'], 'success')
            self.assertIn('1 ticket(s) imported successfully', res_new['params']['message'])

    def test_action_import_tickets_fetch_error(self):
        wizard = self.wizard_model.create({
            'start_date': date(2026, 11, 1),
            'end_date': date(2026, 11, 5),
        })
        with patch.object(self.wizard_cls, '_fetch_zendesk_tickets', side_effect=UserError('Zendesk timeout')):
            res = wizard.action_import_tickets()
            self.assertEqual(res['params']['type'], 'danger')
            self.assertIn('Zendesk timeout', res['params']['message'])

    def test_action_export_tickets_success_and_errors(self):
        today = fields.Date.today()
        wizard = self.wizard_model.create({
            'start_date': today - timedelta(days=2),
            'end_date': today + timedelta(days=2),
        })

        # Create two tickets eligible for export with description
        t1 = self.ticket_model.create({
            'subject': 'Export Ticket 1',
            'email': 't1@example.com',
            'description': 'Export description 1',
            'customer_id': self.partner.id,
        })
        t2 = self.ticket_model.create({
            'subject': 'Export Ticket 2',
            'email': 't2@example.com',
            'description': 'Export description 2',
            'customer_id': self.partner.id,
        })

        # 1. Partial failure / error handling
        with patch.object(self.api_cls, '_find_or_create_user', return_value=50), \
             patch.object(self.ticket_cls, 'search', return_value=self.ticket_model.browse([t1.id, t2.id])), \
             patch.object(self.api_cls, '_request', side_effect=[
                 {'ticket': {'id': 9001}},
                 UserError('Zendesk rejected ticket 2'),
             ]):
            res = wizard.action_export_tickets()
            self.assertEqual(res['params']['type'], 'warning')
            self.assertTrue(res['params']['sticky'])
            self.assertIn('Exported with errors', res['params']['title'])
            self.assertEqual(t1.zendesk_ticket_no, '9001')
            self.assertFalse(t2.zendesk_ticket_no)

        # 2. Complete success on remaining ticket t2
        with patch.object(self.api_cls, '_find_or_create_user', return_value=50), \
             patch.object(self.ticket_cls, 'search', return_value=self.ticket_model.browse([t2.id])), \
             patch.object(self.api_cls, '_request', return_value={'ticket': {'id': 9002}}):
            res2 = wizard.action_export_tickets()
            self.assertEqual(res2['params']['type'], 'success')
            self.assertIn('1 ticket(s) exported successfully', res2['params']['message'])
            self.assertEqual(t2.zendesk_ticket_no, '9002')
