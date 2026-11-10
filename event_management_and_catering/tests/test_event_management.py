# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
"""Unit tests for Event Management and Catering module."""
from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


class DummyResponse:
    """Mock HTTP response object for report testing."""

    def __init__(self):
        self.data = b''

    def set_data(self, data):
        self.data = data


@tagged('post_install', '-at_install', 'event_management_and_catering')
class TestEventManagement(TransactionCase):
    """Test suite for event_management_and_catering module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        # Ensure sales journal with income account exists
        cls.sale_journal = cls.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', cls.company.id),
        ], limit=1)
        if not cls.sale_journal:
            cls.sale_journal = cls.env['account.journal'].create({
                'name': 'Customer Invoices Test',
                'code': 'TESTS',
                'type': 'sale',
                'company_id': cls.company.id,
            })

        # Income account
        cls.income_account = cls.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_ids', 'in', cls.company.id),
        ], limit=1)
        if not cls.income_account:
            cls.income_account = cls.env['account.account'].create({
                'name': 'Test Event Sales',
                'code': '400099',
                'account_type': 'income',
                'company_ids': [fields.Command.link(cls.company.id)],
            })

        # Customer partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'John Doe Event Customer',
            'email': 'john.doe@gmail.com',
            'property_account_receivable_id': cls.env['account.account'].search([
                ('account_type', '=', 'asset_receivable'),
                ('company_ids', 'in', cls.company.id),
            ], limit=1).id or cls.income_account.id,
        })

        # Event type
        cls.event_type = cls.env['event.management.type'].create({
            'name': 'Corporate Gala',
        })

        # Catering product
        cls.catering_product = cls.env.ref(
            'event_management_and_catering.catering_service_product',
            raise_if_not_found=False
        )
        if not cls.catering_product:
            cls.catering_product = cls.env['product.product'].create({
                'name': 'Catering Service',
                'type': 'service',
                'property_account_income_id': cls.income_account.id,
            })
        else:
            if not cls.catering_product.property_account_income_id:
                cls.catering_product.property_account_income_id = cls.income_account.id

        # Catering work food items
        cls.food_product = cls.env['product.product'].create({
            'name': 'Buffet Dinner Plate',
            'type': 'consu',
            'lst_price': 50.0,
        })

        # Security groups
        cls.group_manager = cls.env.ref(
            'event_management_and_catering.group_event_catering_manager'
        )
        cls.group_caterer = cls.env.ref(
            'event_management_and_catering.group_event_catering_caterer'
        )

    def test_01_event_creation_and_naming(self):
        """Test event creation, automated naming format, and reference generation."""
        now = fields.Datetime.now()
        event = self.env['event.management'].create({
            'partner_id': self.partner.id,
            'type_of_event_id': self.event_type.id,
            'start_date': now + timedelta(days=2),
            'end_date': now + timedelta(days=2, hours=6),
            'date': fields.Date.today(),
        })

        self.assertTrue(event.reference, "Reference should be generated from sequence.")
        self.assertIn(self.partner.name, event.name)
        self.assertIn(self.event_type.name, event.name)
        self.assertEqual(event.state, 'draft')
        self.assertEqual(event.currency_id, self.company.currency_id)

    def test_02_event_date_validation(self):
        """Test that event start_date must precede end_date."""
        now = fields.Datetime.now()
        with self.assertRaises(UserError):
            self.env['event.management'].create({
                'partner_id': self.partner.id,
                'type_of_event_id': self.event_type.id,
                'start_date': now + timedelta(days=5),
                'end_date': now + timedelta(days=4),
            })

    def test_03_service_lines_validations(self):
        """Test service line date validations and subtotal computations."""
        now = fields.Datetime.now()
        event = self.env['event.management'].create({
            'partner_id': self.partner.id,
            'type_of_event_id': self.event_type.id,
            'start_date': now + timedelta(days=1),
            'end_date': now + timedelta(days=1, hours=8),
        })

        # Date to before Date from
        with self.assertRaises(ValidationError):
            self.env['event.service.line'].create({
                'event_id': event.id,
                'service': 'catering',
                'date_from': now + timedelta(days=1, hours=4),
                'date_to': now + timedelta(days=1, hours=2),
            })

        # Service date_from before event start_date
        with self.assertRaises(ValidationError):
            self.env['event.service.line'].create({
                'event_id': event.id,
                'service': 'catering',
                'date_from': now,
                'date_to': now + timedelta(days=1, hours=3),
            })

        # Service date_to after event end_date
        with self.assertRaises(ValidationError):
            self.env['event.service.line'].create({
                'event_id': event.id,
                'service': 'catering',
                'date_from': now + timedelta(days=1, hours=2),
                'date_to': now + timedelta(days=1, hours=10),
            })

        # Valid service line
        valid_line = self.env['event.service.line'].create({
            'event_id': event.id,
            'service': 'catering',
            'date_from': now + timedelta(days=1, hours=1),
            'date_to': now + timedelta(days=1, hours=5),
            'amount': 250.0,
        })
        self.assertEqual(valid_line.state, 'pending')
        self.assertFalse(valid_line.invoiced)

        event._compute_price_subtotal()
        self.assertEqual(event.price_subtotal, 250.0)

    def test_04_event_confirm_and_catering_lifecycle(self):
        """Test confirming an event, creating catering order, completing works, and invoicing."""
        now = fields.Datetime.now()
        event = self.env['event.management'].create({
            'partner_id': self.partner.id,
            'type_of_event_id': self.event_type.id,
            'start_date': now + timedelta(days=3),
            'end_date': now + timedelta(days=3, hours=8),
        })

        service_line = self.env['event.service.line'].create({
            'event_id': event.id,
            'service': 'catering',
            'date_from': now + timedelta(days=3, hours=1),
            'date_to': now + timedelta(days=3, hours=6),
            'amount': 0.0,
        })

        # 1. Confirm Event
        event.action_event_confirm()
        self.assertEqual(event.state, 'confirm')
        self.assertTrue(event.catering_on)
        self.assertTrue(event.catering_id)
        catering = event.catering_id
        self.assertEqual(catering.parent_event_id, event)
        self.assertEqual(catering.state, 'open')

        # 2. Add catering works
        work_1 = self.env['event.catering.work'].create({
            'catering_id': catering.id,
            'service_id': self.food_product.id,
            'quantity': 10,
            'amount': 50.0,
            'work_status': 'open',
        })
        work_1._onchange_service_id()
        work_1._compute_sub_total()
        self.assertEqual(work_1.sub_total, 500.0)

        work_2 = self.env['event.catering.work'].create({
            'catering_id': catering.id,
            'service_id': self.food_product.id,
            'quantity': 5,
            'amount': 40.0,
            'work_status': 'open',
        })
        work_2._compute_sub_total()
        self.assertEqual(work_2.sub_total, 200.0)

        catering._compute_price_subtotal()
        self.assertEqual(catering.price_subtotal, 700.0)

        # Pending count
        event._compute_catering_pending()
        event._compute_catering_done()
        self.assertEqual(event.catering_pending, 2)
        self.assertEqual(event.catering_done, 0)

        # 3. Trying to complete catering while works are open raises error
        with self.assertRaises(UserError):
            catering.action_catering_done()

        # 4. Mark works as done and complete catering
        work_1.work_status = 'done'
        work_2.work_status = 'done'
        catering.action_catering_done()
        self.assertEqual(catering.state, 'done')
        self.assertEqual(service_line.state, 'done')
        self.assertEqual(service_line.amount, 700.0)

        event._compute_catering_pending()
        event._compute_catering_done()
        self.assertEqual(event.catering_pending, 0)
        self.assertEqual(event.catering_done, 2)

        # 5. Pending invoice check
        event._compute_pending_invoice()
        self.assertTrue(event.pending_invoice)

        # 6. Cannot close event while uninvoiced
        with self.assertRaises(ValidationError):
            event.action_event_close()

        # 7. Create invoice
        action_res = event.action_event_invoice_create()
        self.assertTrue(action_res)
        self.assertEqual(event.state, 'invoice')
        self.assertEqual(event.invoice_count, 1)
        self.assertTrue(service_line.invoiced)

        # 8. View invoice actions
        inv_action = event.action_view_invoice_event()
        self.assertTrue(inv_action)

        catering_action = event.action_view_catering_service()
        self.assertTrue(catering_action)

        # 9. Close event once invoiced
        event.action_event_close()
        self.assertEqual(event.state, 'close')

    def test_05_event_cancel_and_type_counts(self):
        """Test event cancellation and event count calculation on event types."""
        now = fields.Datetime.now()
        event = self.env['event.management'].create({
            'partner_id': self.partner.id,
            'type_of_event_id': self.event_type.id,
            'start_date': now + timedelta(days=2),
            'end_date': now + timedelta(days=2, hours=4),
        })
        self.assertEqual(event.state, 'draft')
        event.action_event_cancel()
        self.assertEqual(event.state, 'cancel')

        self.event_type._compute_event_count()
        self.assertTrue(self.event_type.event_count >= 1)

        action = self.event_type.get_event_type_action_event()
        self.assertTrue(action)

    def test_06_reports_wizard_and_templates(self):
        """Test PDF and XLSX report generation from wizard."""
        now = fields.Datetime.now()
        event = self.env['event.management'].create({
            'partner_id': self.partner.id,
            'type_of_event_id': self.event_type.id,
            'start_date': now + timedelta(days=1),
            'end_date': now + timedelta(days=1, hours=5),
            'date': fields.Date.today(),
        })

        wizard = self.env['event.management.report'].create({
            'date_from': fields.Date.today() - timedelta(days=5),
            'date_to': fields.Date.today() + timedelta(days=5),
            'partner_id': self.partner.id,
            'type_event_ids': [fields.Command.link(self.event_type.id)],
            'event_state': 'draft',
        })

        # Date validation on wizard
        with self.assertRaises(ValidationError):
            invalid_wizard = self.env['event.management.report'].create({
                'date_from': fields.Date.today() + timedelta(days=10),
                'date_to': fields.Date.today(),
            })
            invalid_wizard.action_print_xls_report()

        # PDF Action
        pdf_action = wizard.action_print_pdf_report()
        self.assertTrue(pdf_action)

        # PDF report values computation
        report_model = self.env['report.event_management_and_catering.report_event_management']
        report_vals = report_model._get_report_values(
            docids=[],
            data={'form': wizard.read()[0], 'event_types': [self.event_type.id]}
        )
        self.assertIn('docs', report_vals)
        self.assertIn('today_date', report_vals)

        # XLSX Action and file generation
        xls_action = wizard.action_print_xls_report()
        self.assertEqual(xls_action.get('report_type'), 'xlsx')

        dummy_resp = DummyResponse()
        wizard_options = {
            'event_type': [self.event_type.id],
            'date_from': fields.Date.to_string(fields.Date.today() - timedelta(days=5)),
            'date_to': fields.Date.to_string(fields.Date.today() + timedelta(days=5)),
            'customer': self.partner.id,
            'state': 'draft',
            'today_date': '2026-11-09 10:00:00',
            'company': [self.company.name, 'Main Street'],
        }
        wizard.get_xlsx_report(wizard_options, dummy_resp)
        self.assertTrue(len(dummy_resp.data) > 0, "XLSX report data should be generated")

