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

from datetime import date

from odoo import Command
from odoo.tests.common import TransactionCase


class TestFleetRentalLine(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Fleet Rental Customer',
            'company_id': False,
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
    def _create_invoice(cls, **values):
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
        defaults.update(values)
        return cls.env['account.move'].create(defaults)

    def test_compute_payment_info_uses_invoice_state(self):
        invoice = self._create_invoice()
        rental_line = self.env['fleet.rental.line'].create({
            'name': 'Rental recurring line',
            'invoice_number': invoice.id,
            'invoice_ref': invoice.id,
        })

        rental_line._compute_payment_info()

        self.assertEqual(rental_line.payment_info, invoice.payment_state or invoice.state)
