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

from odoo import Command, fields
from odoo.tests.common import TransactionCase


class TestAccountMoveLine(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Date.today()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Fleet Rental Customer',
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
            'license_plate': 'RENT-TEST-002',
            'vin_sn': 'RENTVIN002',
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

    def test_onchange_price_unit_updates_first_payment_for_first_invoice(self):
        contract = self._create_contract(first_payment=10.0)
        invoice = self._create_invoice(contract, is_first_invoice=True)
        line = invoice.invoice_line_ids[:1]

        line.price_unit = 75.0
        line._onchange_price_unit()

        self.assertEqual(contract.first_payment, 75.0)

    def test_onchange_price_unit_ignores_regular_invoice(self):
        contract = self._create_contract(first_payment=10.0)
        invoice = self._create_invoice(contract, is_first_invoice=False)
        line = invoice.invoice_line_ids[:1]

        line.price_unit = 75.0
        line._onchange_price_unit()

        self.assertEqual(contract.first_payment, 10.0)
