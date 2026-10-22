# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Safa KB(odoo@cybrosys.com)
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
#############################################################################
from datetime import date, timedelta
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAccountMove(TransactionCase):
    """Test cases for account.move inheritance."""

    def setUp(self):
        super().setUp()
        self.customer = self.env['res.partner'].create({'name': 'Invoice Cust'})
        self.state = self.env['res.country.state'].create({
            'name': 'Invoice State',
            'code': 'IV',
            'country_id': self.env.ref('base.us').id,
        })
        self.shift = self.env['cleaning.shift'].create({
            'shift_type': 'Morning Shift',
            'shift_time_from': 8.0,
            'shift_time_to': 16.0,
        })
        self.leader_emp = self.env['hr.employee'].create({'name': 'Leader'})
        self.leader_detail = self.env['employee.details'].create({
            'employee_name_id': self.leader_emp.id,
            'time_shift_id': self.shift.id,
        })
        self.team = self.env['cleaning.team'].create({
            'name': 'Invoice Team',
            'team_leader_id': self.leader_detail.id,
            'members_ids': [(6, 0, [self.leader_detail.id])],
            'duty_type': 'morning',
        })
        self.booking = self.env['cleaning.booking'].create({
            'customer_name_id': self.customer.id,
            'address': 'Invoice Address',
            'building_type_id': self.env['building.type'].create(
                {'name': 'House'}).id,
            'cleaning_date': date.today() + timedelta(days=1),
            'cleaning_time': 'morning',
            'cleaning_team_id': self.team.id,
            'location_state_id': self.state.id,
            'unit_price': 50.0,
        })

    def test_cleaning_id_field(self):
        """Test cleaning_id field on account.move."""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.customer.id,
            'cleaning_id': self.booking.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Cleaning Service',
                'price_unit': 100.0,
            })],
        })
        self.assertEqual(invoice.cleaning_id, self.booking)

    def test_invoice_paid_hook_posts_message(self):
        """Test that paying an invoice posts a message on booking."""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.customer.id,
            'cleaning_id': self.booking.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Cleaning Service',
                'price_unit': 100.0,
            })],
        })
        invoice.action_post()
        # Register payment to make it paid
        payment_register = self.env['account.payment.register'].with_context(
            active_model='account.move', active_ids=invoice.ids
        ).create({
            'amount': invoice.amount_total,
        })
        payment_register._create_payments()
        invoice.invalidate_recordset()
        # Check that a message was posted on the booking
        messages = self.booking.message_ids.filtered(
            lambda m: 'Invoice' in (m.body or '') and 'paid' in (m.body or ''))
        self.assertTrue(messages)