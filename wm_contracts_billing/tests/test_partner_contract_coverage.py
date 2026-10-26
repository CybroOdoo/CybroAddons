#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, TransactionCase, tagged


@tagged('post_install', '-at_install', 'wm_billing')
class TestPartnerContractCoverage(TransactionCase):
    """Contract constraints, lifecycle actions, expiry and collection order generation crons."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Date.today()
        cls.partner = cls.env['res.partner'].create({'name': 'Contract Coverage Customer'})
        cls.point = cls.env['wm.collection.point'].create({
            'name': 'Contract Coverage Site', 'partner_id': cls.partner.id})
        cls.point2 = cls.env['wm.collection.point'].create({
            'name': 'Contract Coverage Site 2', 'partner_id': cls.partner.id})
        cls.category = cls.env['wm.waste.category'].create({'name': 'Cov Cat', 'code': 'COVCAT'})
        cls.sla = cls.env['wm.sla'].create({'name': 'Cov SLA', 'terms_and_conditions': 'T'})

    def _contract(self, **kw):
        vals = {
            'partner_id': self.partner.id,
            'sla_id': self.sla.id,
            'from_date': self.today - timedelta(days=5),
            'to_date': self.today + timedelta(days=100),
            'frequency': 'monthly',
            'no_of_frequency': 1,
            'billing_basis': 'per_collection',
            'fixed_price': 100.0,
            'max_weight': 500.0,
            'overweight_price': 10.0,
        }
        vals.update(kw)
        return self.env['wm.partner.contract'].create(vals)

    def _line(self, price=1.0):
        return (0, 0, {'category_id': self.category.id, 'price': price})

    # Constraints
    def test_dates_constraint(self):
        with self.assertRaises(ValidationError):
            self._contract(to_date=self.today - timedelta(days=30))

    def test_pricing_constraints(self):
        with self.assertRaises(ValidationError):
            self._contract(fixed_price=0.0)
        with self.assertRaises(ValidationError):
            self._contract(max_weight=0.0)
        with self.assertRaises(ValidationError):
            self._contract(overweight_price=0.0)
        hybrid = dict(billing_basis='hybrid', included_weight=50.0)
        self._contract(**hybrid)
        with self.assertRaises(ValidationError):
            self._contract(**dict(hybrid, included_weight=0.0))
        with self.assertRaises(ValidationError):
            self._contract(**dict(hybrid, fixed_price=0.0))
        with self.assertRaises(ValidationError):
            self._contract(billing_basis='category_rate')
        with self.assertRaises(ValidationError):
            self._contract(billing_basis='category_rate', contract_line_ids=[self._line(0.0)])
        self._contract(billing_basis='category_rate', contract_line_ids=[self._line(1.5)])
        with self.assertRaises(ValidationError):
            self._contract(billing_basis='material')
        with self.assertRaises(ValidationError):
            self._contract(billing_basis='material', contract_line_ids=[self._line(-1.0)])
        self._contract(billing_basis='material', contract_line_ids=[self._line(0.0)])

    def test_frequency_limits(self):
        with self.assertRaises(ValidationError):
            self._contract(no_of_frequency=0)
        with self.assertRaises(ValidationError):
            self._contract(frequency='weekly', no_of_frequency=8)
        with self.assertRaises(ValidationError):
            self._contract(frequency='daily', no_of_frequency=11)
        self._contract(frequency='monthly', no_of_frequency=31)

    def test_monthly_day_bounds(self):
        with self.assertRaises(ValidationError):
            self._contract(monthly_option='date', day_of_month=32)
        with self.assertRaises(ValidationError):
            self._contract(monthly_option='date', day_of_month=0)
        self._contract(monthly_option='last_day', day_of_month=0)

    def test_unique_active_contract_per_site(self):
        self._contract(state='ongoing', collection_point_ids=[(6, 0, self.point.ids)])
        with self.assertRaises(ValidationError):
            self._contract(state='confirmed', collection_point_ids=[(6, 0, self.point.ids)])
        # a draft contract on the same site and another site are fine
        self._contract(state='draft', collection_point_ids=[(6, 0, self.point.ids)])
        self._contract(state='ongoing', collection_point_ids=[(6, 0, self.point2.ids)])

    def test_unique_contract_per_customer_overlap(self):
        self._contract(state='ongoing', collection_point_ids=[(6, 0, self.point.ids)])
        with self.assertRaises(ValidationError):
            self._contract(state='ongoing', collection_point_ids=[(6, 0, (self.point | self.point2).ids)])

    def test_onchange_weekdays_sets_frequency_count(self):
        form = Form(self.env['wm.partner.contract'])
        form.frequency = 'weekly'
        form.monday = True
        form.wednesday = True
        form.friday = True
        self.assertEqual(form.no_of_frequency, 3)

    # Computes
    def test_expiry_status_and_from_date_passed(self):
        self.assertEqual(self._contract().get_expiry_status(), 'active')
        self.assertEqual(self._contract(
            from_date=self.today + timedelta(days=3),
            to_date=self.today + timedelta(days=9)).get_expiry_status(), 'pending')
        expired = self._contract(from_date=self.today - timedelta(days=9), to_date=self.today - timedelta(days=2))
        self.assertEqual(expired.get_expiry_status(), 'expired')
        self.assertTrue(expired.is_from_date_passed)
        starting_today = self._contract(from_date=self.today)
        self.assertFalse(starting_today.is_from_date_passed)

    def test_selected_products_compute(self):
        contract = self._contract(billing_basis='material', contract_line_ids=[self._line(1.0)])
        self.assertEqual(contract.selected_product_ids, self.category)

    # State transitions
    def test_price_lock_after_confirmation(self):
        contract = self._contract(state='confirmed')
        with self.assertRaises(UserError):
            contract.fixed_price = 250.0
        contract.with_context(wm_contract_price_override=True).fixed_price = 250.0
        self.assertEqual(contract.fixed_price, 250.0)
        draft = self._contract()
        draft.fixed_price = 300.0

    def test_confirm_requires_signed_valid_contract(self):
        contract = self._contract(contract_line_ids=[self._line()])
        with self.assertRaises(UserError):
            contract.action_confirm()
        contract.state = 'signed'
        contract.action_confirm()
        self.assertEqual(contract.state, 'confirmed')
        self.assertTrue(contract.sla_snapshot_html)
        no_line = self._contract(state='signed')
        with self.assertRaises(ValidationError):
            no_line.action_confirm()
        stale = self._contract(state='signed', contract_line_ids=[self._line()],
                               from_date=self.today - timedelta(days=9), to_date=self.today - timedelta(days=1))
        with self.assertRaises(ValidationError):
            stale.action_confirm()

    def test_start_only_from_confirmed(self):
        contract = self._contract()
        with self.assertRaises(UserError):
            contract.action_start()
        contract.state = 'confirmed'
        contract.action_start()
        self.assertEqual(contract.state, 'ongoing')

    def test_cancel_and_reset_to_draft(self):
        contract = self._contract()
        with self.assertRaises(UserError):
            contract.action_reset_to_draft()
        contract.action_cancel()
        self.assertEqual(contract.state, 'cancelled')
        with self.assertRaises(UserError):
            contract.action_cancel()
        contract.action_reset_to_draft()
        self.assertEqual(contract.state, 'draft')
        expired = self._contract(state='expired')
        with self.assertRaises(UserError):
            expired.action_cancel()

    def test_mark_as_sent_snapshots_sla(self):
        contract = self._contract()
        contract.with_context(mark_contract_as_sent=True).message_post(body='hello')
        self.assertEqual(contract.state, 'sent')
        self.assertTrue(contract.sla_snapshot_html)

    # Crons
    def test_cron_expire_contracts(self):
        past = dict(from_date=self.today - timedelta(days=30), to_date=self.today - timedelta(days=1))
        ongoing = self._contract(state='ongoing', **past)
        sent = self._contract(state='sent', **past)
        draft = self._contract(state='draft', **past)
        other = self.env['res.partner'].create({'name': 'Other Cov Customer'})
        current = self._contract(state='ongoing', partner_id=other.id)
        self.env['wm.partner.contract']._cron_expire_contracts()
        self.assertEqual(ongoing.state, 'expired')
        self.assertEqual(sent.state, 'expired')
        self.assertEqual(draft.state, 'draft')
        self.assertEqual(current.state, 'ongoing')

    def test_is_contract_due(self):
        Contract = self.env['wm.partner.contract']
        contract = self._contract(frequency='daily', no_of_frequency=1)
        self.assertTrue(Contract._is_contract_due(contract, self.today))
        self.assertFalse(Contract._is_contract_due(contract, self.today - timedelta(days=30)))
        contract.last_generated_date = self.today
        self.assertFalse(Contract._is_contract_due(contract, self.today))
        self.assertTrue(Contract._is_contract_due(contract, self.today + timedelta(days=1)))
        contract.frequency = 'weekly'
        contract.last_generated_date = self.today - timedelta(days=self.today.weekday())
        self.assertFalse(Contract._is_contract_due(contract, self.today))
        self.assertTrue(Contract._is_contract_due(contract, self.today + timedelta(days=7)))
        contract.frequency = 'monthly'
        contract.last_generated_date = self.today.replace(day=1)
        self.assertFalse(Contract._is_contract_due(contract, self.today))
        self.assertTrue(Contract._is_contract_due(contract, self.today.replace(day=28) + timedelta(days=10)))

    def test_cron_generate_collection_orders_daily(self):
        contract = self._contract(
            state='ongoing', frequency='daily', no_of_frequency=2,
            collection_point_ids=[(6, 0, self.point.ids)])
        Contract = self.env['wm.partner.contract']
        Contract._cron_generate_collection_orders()
        orders = self.env['wm.collection.order'].search([('contract_id', '=', contract.id)])
        self.assertEqual(len(orders), 2)
        self.assertEqual(orders.collection_point_id, self.point)
        self.assertEqual(contract.last_generated_date, self.today)
        # Not due again on the same day: no duplicates
        Contract._cron_generate_collection_orders()
        self.assertEqual(self.env['wm.collection.order'].search_count([('contract_id', '=', contract.id)]), 2)

    def test_cron_generate_skips_inactive_contracts(self):
        draft = self._contract(state='draft', frequency='daily', collection_point_ids=[(6, 0, self.point.ids)])
        future = self._contract(state='ongoing', frequency='daily', collection_point_ids=[(6, 0, self.point2.ids)],
                                from_date=self.today + timedelta(days=5),
                                to_date=self.today + timedelta(days=50))
        self.env['wm.partner.contract']._cron_generate_collection_orders()
        self.assertFalse(self.env['wm.collection.order'].search_count([('contract_id', 'in', (draft | future).ids)]))

    def test_generate_weekly_uses_selected_weekdays(self):
        contract = self._contract(
            state='ongoing', frequency='weekly', no_of_frequency=1,
            monday=True, tuesday=True, wednesday=True, thursday=True,
            friday=True, saturday=True, sunday=True,
            collection_point_ids=[(6, 0, self.point.ids)])
        contract._generate_collection_orders(self.today)
        orders = self.env['wm.collection.order'].search([('contract_id', '=', contract.id)])
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders.scheduled_start.date(), self.today)

    def test_generate_monthly_last_day(self):
        contract = self._contract(
            state='ongoing', frequency='monthly', no_of_frequency=1, monthly_option='last_day',
            collection_point_ids=[(6, 0, self.point.ids)])
        contract._generate_collection_orders(self.today)
        order = self.env['wm.collection.order'].search([('contract_id', '=', contract.id)])
        next_month = self.today.replace(day=28) + timedelta(days=4)
        last_day = next_month - timedelta(days=next_month.day)
        self.assertEqual(order.scheduled_start.date(), last_day)
