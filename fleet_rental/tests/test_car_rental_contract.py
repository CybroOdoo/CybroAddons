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

from datetime import date, timedelta
from unittest.mock import patch

from odoo import Command, fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestCarRentalContract(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Date.today()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Fleet Rental Customer',
            'email': 'customer@example.com',
            'company_id': False,
        })
        brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'Rental Brand',
        })
        vehicle_model = cls.env['fleet.vehicle.model'].create({
            'name': 'Rental Model',
            'brand_id': brand.id,
        })
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': vehicle_model.id,
            'license_plate': 'RENT-TEST-004',
            'vin_sn': 'RENTVIN004',
            'state_id': cls.env.ref('fleet_rental.vehicle_state_active').id,
        })
        account_domain = cls.env['account.account']._check_company_domain(cls.env.company)
        journal_domain = cls.env['account.journal']._check_company_domain(cls.env.company)
        cls.sale_journal = cls.env['account.journal'].search([
            *journal_domain,
            ('type', '=', 'sale'),
        ], limit=1)
        cls.income_account = cls.env['account.account'].search([
            *account_domain,
            ('account_type', '=', 'income'),
            ('deprecated', '=', False),
        ], limit=1)
        cls.env.ref('fleet_rental.fleet_service_product').property_account_income_id = cls.income_account

    @classmethod
    def _create_contract(cls, **values):
        defaults = {
            'customer_id': cls.partner.id,
            'vehicle_id': cls.vehicle.id,
            'cost': 100.0,
            'cost_generated': 25.0,
            'cost_frequency': 'daily',
            'first_payment': 40.0,
            'rent_start_date': cls.today,
            'rent_end_date': cls.today + timedelta(days=3),
            'journal_type': cls.sale_journal.id,
            'account_type': cls.income_account.id,
        }
        defaults.update(values)
        return cls.env['car.rental.contract'].create(defaults)

    @classmethod
    def _create_invoice(cls, contract=None, **values):
        defaults = {
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'journal_id': cls.sale_journal.id,
            'invoice_date': date.today(),
            'invoice_line_ids': [Command.create({
                'name': 'Rental invoice line',
                'quantity': 1.0,
                'price_unit': 50.0,
                'account_id': cls.income_account.id,
            })],
        }
        if contract:
            defaults['fleet_rent_id'] = contract.id
        defaults.update(values)
        return cls.env['account.move'].create(defaults)

    def test_action_run_sets_contract_running_and_vehicle_rent_state(self):
        contract = self._create_contract()

        contract.action_run()

        self.assertEqual(contract.state, 'running')
        self.assertEqual(
            contract.vehicle_id.state_id,
            self.env.ref('fleet_rental.vehicle_state_rent'),
        )

    def test_invalid_rent_dates_raise_user_error(self):
        with self.assertRaises(UserError):
            self._create_contract(
                rent_start_date=self.today,
                rent_end_date=self.today - timedelta(days=1),
            )

    def test_hourly_rent_requires_end_time_after_start_time_on_same_day(self):
        with self.assertRaises(ValidationError):
            self._create_contract(
                is_rent_by_hour=True,
                start_time='10:00',
                end_time='09:00',
                rent_start_date=self.today,
                rent_end_date=self.today,
            )

    def test_checklist_totals_and_verification_flags_are_computed(self):
        contract = self._create_contract(damage_cost=30.0)
        tool = self.env['car.tools'].create({
            'name': 'Jack',
            'price': 70.0,
        })
        self.env['car.rental.checklist'].create({
            'name': tool.id,
            'price': tool.price,
            'is_checklist_active': False,
            'checklist_number': contract.id,
        })

        contract._compute_total()
        contract._compute_is_check_verify()

        self.assertEqual(contract.total, 70.0)
        self.assertEqual(contract.tools_missing_cost, 70.0)
        self.assertEqual(contract.damage_cost_sub, 30.0)
        self.assertEqual(contract.total_cost, 100.0)
        self.assertFalse(contract.is_check_verify)

    def test_action_confirm_reserves_vehicle_and_action_cancel_releases_it(self):
        contract = self._create_contract()
        Mail = type(self.env['mail.mail'])

        with patch.object(Mail, 'send', return_value=True):
            contract.action_confirm()

        self.assertEqual(contract.state, 'reserved')
        self.assertTrue(contract.reserved_fleet_id)
        self.assertFalse(contract.vehicle_id.is_rental_check_availability)
        self.assertNotEqual(contract.name, 'Draft Contract')

        contract.action_cancel()

        self.assertEqual(contract.state, 'cancel')
        self.assertTrue(contract.vehicle_id.is_rental_check_availability)
        self.assertFalse(contract.reserved_fleet_id.exists())

    def test_action_confirm_rejects_overlapping_reservation(self):
        existing_contract = self._create_contract()
        Mail = type(self.env['mail.mail'])
        with patch.object(Mail, 'send', return_value=True):
            existing_contract.action_confirm()
        overlapping_contract = self._create_contract(
            rent_start_date=self.today + timedelta(days=1),
            rent_end_date=self.today + timedelta(days=2),
        )

        with self.assertRaises(UserError):
            overlapping_contract.action_confirm()

    def test_action_invoice_create_creates_first_invoice_and_returns_action(self):
        contract = self._create_contract(cost_frequency='no')

        result = contract.action_invoice_create()

        invoice = contract.first_payment_inv
        self.assertEqual(result['res_id'], invoice.id)
        self.assertTrue(contract.is_first_invoice_created)
        self.assertTrue(invoice.is_first_invoice)
        self.assertEqual(invoice.fleet_rent_id, contract)
        self.assertEqual(invoice.invoice_line_ids.price_unit, contract.first_payment)

    def test_invoice_count_and_action_view_invoice_use_related_invoices(self):
        contract = self._create_contract()
        invoice = self._create_invoice(contract)

        contract._compute_invoice_count()
        action = contract.action_view_invoice()

        self.assertEqual(contract.invoice_count, 1)
        self.assertEqual(action['res_id'], invoice.id)
        self.assertEqual(action['res_model'], 'account.move')

    def test_action_force_checking_and_done_require_paid_invoices(self):
        contract = self._create_contract(state='running')
        self._create_invoice(contract)

        with self.assertRaises(UserError):
            contract.action_force_checking()
        with self.assertRaises(UserError):
            contract.action_set_to_done()

        self.env['account.move'].search([('fleet_rent_id', '=', contract.id)]).unlink()
        contract.action_force_checking()
        self.assertEqual(contract.state, 'checking')
        contract.action_set_to_done()
        self.assertEqual(contract.state, 'done')

    def test_action_verify_creates_damage_invoice_and_releases_vehicle(self):
        contract = self._create_contract(damage_cost=55.0)
        reservation = self.env['rental.fleet.reserved'].create({
            'customer_id': self.partner.id,
            'date_from': contract.rent_start_date,
            'date_to': contract.rent_end_date,
            'reserved_obj_id': self.vehicle.id,
        })
        contract.reserved_fleet_id = reservation
        contract.vehicle_id.is_rental_check_availability = False
        contract._compute_total()

        result = contract.action_verify()

        self.assertEqual(result['type'], 'ir.actions.act_window_close')
        self.assertEqual(contract.state, 'invoice')
        self.assertFalse(reservation.exists())
        self.assertTrue(contract.vehicle_id.is_rental_check_availability)
        damage_invoice = self.env['account.move'].search([
            ('fleet_rent_id', '=', contract.id),
            ('invoice_origin', '=', contract.name),
        ])
        self.assertEqual(damage_invoice.invoice_line_ids.price_unit, 55.0)

    def test_extend_rent_flow_validates_and_updates_reservation_date(self):
        contract = self._create_contract()
        reservation = self.env['rental.fleet.reserved'].create({
            'customer_id': self.partner.id,
            'date_from': contract.rent_start_date,
            'date_to': contract.rent_end_date,
            'reserved_obj_id': self.vehicle.id,
        })
        contract.reserved_fleet_id = reservation

        contract.action_extend_rent()
        self.assertTrue(contract.is_read_only)

        with self.assertRaises(ValidationError):
            contract.rent_end_date = reservation.date_to

        new_end_date = reservation.date_to + timedelta(days=2)
        contract.rent_end_date = new_end_date
        contract.action_confirm_extend_rent()

        self.assertFalse(contract.is_read_only)
        self.assertEqual(reservation.date_to, new_end_date)

        contract.action_extend_rent()
        contract.rent_end_date = new_end_date + timedelta(days=1)
        contract.action_discard_extend()

        self.assertFalse(contract.is_read_only)
        self.assertEqual(contract.rent_end_date, reservation.date_to)

    def test_fleet_scheduler1_creates_recurring_invoice_and_line(self):
        contract = self._create_contract(state='running')
        Mail = type(self.env['mail.mail'])

        with patch.object(Mail, 'send', return_value=True):
            contract.fleet_scheduler1(self.today)

        invoice = self.env['account.move'].search([
            ('fleet_rent_id', '=', contract.id),
            ('invoice_origin', '=', contract.name),
        ])
        recurring_line = self.env['fleet.rental.line'].search([
            ('rental_number', '=', contract.id),
            ('invoice_ref', '=', invoice.id),
        ])
        self.assertEqual(invoice.invoice_line_ids.price_unit, contract.cost_generated)
        self.assertEqual(recurring_line.recurring_amount, contract.cost_generated)

    def test_fleet_scheduler_moves_expired_running_contract_to_checking(self):
        contract = self._create_contract(
            state='running',
            rent_start_date=self.today - timedelta(days=5),
            rent_end_date=self.today - timedelta(days=1),
        )

        with mute_logger('odoo.models.unlink'):
            self.env['car.rental.contract'].fleet_scheduler()

        self.assertEqual(contract.state, 'checking')
