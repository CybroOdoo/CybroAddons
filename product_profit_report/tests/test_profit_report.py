# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mruthul (odoo@cybrosys.com)
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
from odoo import fields
from odoo.tests import tagged
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged('post_install', '-at_install')
class TestProductProfitReport(AccountTestInvoicingCommon):
    """Tests for the product profit report"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category = cls.env['product.category'].create({
            'name': 'Test Category',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'categ_id': cls.category.id,
            'standard_price': 50.0,
            'lst_price': 100.0,
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Test Partner'})
        cls.report_model = cls.env[
            'report.product_profit_report.product_profit_report']

    def _post_move(self, move_type, qty, price, discount=0.0):
        move = self.env['account.move'].create({
            'move_type': move_type,
            'partner_id': self.partner.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': qty,
                'price_unit': price,
                'discount': discount,
            })],
        })
        move.action_post()
        return move

    def _get_stats(self):
        wizard = self.env['profit.product'].create({
            'from_date': fields.Date.today(),
            'to_date': fields.Date.today(),
            'categ_id': self.category.id,
            'company_id': self.env.company.id,
        })
        wizard._onchange_categ_id()
        values = self.report_model.generate_report_values(wizard.read([])[0])
        return values['groups'].get(self.product.id)

    def test_01_profit_report_basic(self):
        """Profit uses the standard price when there is no history"""
        self._post_move('out_invoice', 2, 120.0)
        stats = self._get_stats()
        self.assertEqual(stats['qty'], 2)
        self.assertEqual(stats['sales'], 240.0)
        self.assertEqual(stats['expense'], 100.0)
        self.assertEqual(stats['profit'], 140.0)

    def test_02_profit_report_with_history(self):
        """Profit uses the price history when it exists"""
        self.env['price.history'].create({
            'product_id': self.product.id,
            'cost': 60.0,
            'datetime': fields.Datetime.now(),
            'company_id': self.env.company.id,
        })
        self._post_move('out_invoice', 3, 150.0)
        stats = self._get_stats()
        self.assertEqual(stats['qty'], 3)
        self.assertEqual(stats['sales'], 450.0)
        self.assertEqual(stats['expense'], 180.0)
        self.assertEqual(stats['profit'], 270.0)

    def test_03_profit_report_refund(self):
        """A customer refund gives negative figures"""
        self._post_move('out_refund', 1, 100.0)
        stats = self._get_stats()
        self.assertEqual(stats['qty'], -1)
        self.assertEqual(stats['sales'], -100.0)
        self.assertEqual(stats['expense'], -50.0)
        self.assertEqual(stats['profit'], -50.0)

    def test_04_profit_report_discount(self):
        """The discount is applied as a percentage"""
        self._post_move('out_invoice', 2, 100.0, discount=10.0)
        stats = self._get_stats()
        self.assertEqual(stats['sales'], 180.0)
        self.assertEqual(stats['profit'], 80.0)

    def test_05_profit_report_uom_conversion(self):
        """Cost and quantity use the product UoM, not the line UoM"""
        dozen = self.env.ref('uom.product_uom_dozen')
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_id': dozen.id,
                'quantity': 1,
                'price_unit': 1200.0,
            })],
        })
        move.action_post()
        stats = self._get_stats()
        self.assertEqual(stats['qty'], 12)
        self.assertEqual(stats['unit'], self.product.uom_id.name)
        self.assertEqual(stats['sales'], 1200.0)
        self.assertEqual(stats['expense'], 600.0)
        self.assertEqual(stats['profit'], 600.0)

    def test_06_standard_price_change_is_logged(self):
        """Changing the standard price creates a history record"""
        history = self.env['price.history']
        domain = [('product_id', '=', self.product.id)]
        self.assertEqual(history.search(domain, limit=1).cost, 50.0)
        self.product.standard_price = 80.0
        self.assertEqual(history.search(domain, limit=1).cost, 80.0)
        count = history.search_count(domain)
        self.product.standard_price = 80.0
        self.assertEqual(history.search_count(domain), count)
        self._post_move('out_invoice', 1, 200.0)
        stats = self._get_stats()
        self.assertEqual(stats['expense'], 80.0)
        self.assertEqual(stats['profit'], 120.0)

    def test_07_price_history_defaults(self):
        """Price history defaults to the current company"""
        history = self.env['price.history'].create({
            'product_id': self.product.id,
            'cost': 10.0,
        })
        self.assertEqual(history.company_id, self.env.company)
        self.assertEqual(
            self.product.get_history_price(self.env.company.id), 10.0)
