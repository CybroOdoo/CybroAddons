# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

from io import BytesIO
from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPoFourwayMatchReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Vendor',
            'supplier_rank': 1,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'purchase_ok': True,
        })
        cls.purchase_order = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [Command.create({
                'product_id': cls.product.id,
                'name': 'Test Product',
                'product_qty': 2,
                'price_unit': 100,
                'date_planned': '2026-01-01 00:00:00',
            })]
        })

    def test_onchange_partner_id(self):
        """Test onchange clears purchase orders."""
        wizard = self.env['fourway.report'].create({
            'partner_id': self.partner.id,
            'order_ids': [Command.link(self.purchase_order.id)]
        })
        wizard._onchange_partner_id()
        self.assertFalse(wizard.order_ids)

    def test_print_xlsx(self):
        """Test xlsx report action."""
        wizard = self.env['fourway.report'].create({
            'partner_id': self.partner.id,
            'order_ids': [Command.link(self.purchase_order.id)]
        })
        action = wizard.print_xlsx()
        self.assertEqual(
            action['type'],
            'ir.actions.report'
        )
        self.assertEqual(
            action['report_type'],
            'xlsx'
        )
        self.assertEqual(
            action['data']['model'],
            'fourway.report'
        )

    def test_get_xlsx_report(self):
        """Test xlsx report generation."""
        wizard = self.env['fourway.report'].create({
            'partner_id': self.partner.id,
            'order_ids': [Command.link(self.purchase_order.id)]
        })
        data = {
            'partner_id': self.partner.id,
            'order_ids': [self.purchase_order.id],
        }
        class MockResponse:
            stream = BytesIO()
        response = MockResponse()
        wizard.get_xlsx_report(
            data,
            response
        )
        self.assertTrue(
            response.stream.getvalue()
        )
