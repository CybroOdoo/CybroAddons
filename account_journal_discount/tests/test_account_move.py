# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Vivek @ cybrosys,(odoo@cybrosys.com)
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

from odoo import Command, fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestAccountJournalDiscount(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.discount_income_account = cls.env['account.account'].create({
            'code': 'XDISCOUNTIN',
            'name': 'Customer Discount Account - Test',
            'account_type': 'income',
        })
        cls.discount_expense_account = cls.env['account.account'].create({
            'code': 'XDISCOUNTOUT',
            'name': 'Vendor Discount Account - Test',
            'account_type': 'expense',
        })
        cls.customer = cls.partner_a

        cls.discount_category = cls.env['product.category'].create({
            'name': 'Discountable Products',
            'customer_account_discount_id': cls.discount_income_account.id,
            'vendor_account_discount_id': cls.discount_expense_account.id,
        })
        cls.discount_product = cls.env['product.product'].create({
            'name': 'Discounted Service',
            'type': 'service',
            'categ_id': cls.discount_category.id,
            'uom_id': cls.env.ref('uom.product_uom_unit').id,
            'uom_po_id': cls.env.ref('uom.product_uom_unit').id,
            'lst_price': 100.0,
            'standard_price': 60.0,
            'property_account_income_id': cls.company_data['default_account_revenue'].id,
            'property_account_expense_id': cls.company_data['default_account_expense'].id,
        })

    def _create_invoice(self, move_type, journal, price_unit=100.0, discount=10.0):
        return self.env['account.move'].create({
            'move_type': move_type,
            'partner_id': self.customer.id,
            'journal_id': journal.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [Command.create({
                'product_id': self.discount_product.id,
                'name': self.discount_product.name,
                'quantity': 1.0,
                'price_unit': price_unit,
                'discount': discount,
                'account_id': (
                    self.discount_product.property_account_income_id.id
                    if move_type == 'out_invoice'
                    else self.discount_product.property_account_expense_id.id
                ),
            })],
        })

    def test_customer_discount_lines_are_added_on_post(self):
        invoice = self._create_invoice('out_invoice', self.company_data['default_journal_sale'])

        invoice.action_post()

        discount_lines = invoice.line_ids.filtered(
            lambda line: line.account_id == self.discount_income_account
            and line.display_type == 'tax'
        )
        counterpart_lines = invoice.line_ids.filtered(
            lambda line: line.account_id == self.discount_product.property_account_income_id
            and line.display_type == 'tax'
        )

        self.assertEqual(len(discount_lines), 1)
        self.assertEqual(len(counterpart_lines), 1)
        self.assertEqual(discount_lines.debit, 10.0)
        self.assertEqual(discount_lines.credit, 0.0)
        self.assertEqual(counterpart_lines.credit, 10.0)
        self.assertEqual(counterpart_lines.debit, 0.0)

    def test_vendor_discount_lines_are_added_on_post(self):
        bill = self._create_invoice('in_invoice', self.company_data['default_journal_purchase'])

        bill.action_post()

        discount_lines = bill.line_ids.filtered(
            lambda line: line.account_id == self.discount_expense_account
            and line.display_type == 'tax'
        )
        counterpart_lines = bill.line_ids.filtered(
            lambda line: line.account_id == self.discount_product.property_account_expense_id
            and line.display_type == 'tax'
        )

        self.assertEqual(len(discount_lines), 1)
        self.assertEqual(len(counterpart_lines), 1)
        self.assertEqual(discount_lines.debit, 10.0)
        self.assertEqual(discount_lines.credit, 0.0)
        self.assertEqual(counterpart_lines.credit, 10.0)
        self.assertEqual(counterpart_lines.debit, 0.0)

    def test_no_discount_lines_are_added_without_discount(self):
        invoice = self._create_invoice('out_invoice', self.company_data['default_journal_sale'], discount=0.0)

        invoice.action_post()

        discount_lines = invoice.line_ids.filtered(
            lambda line: line.account_id == self.discount_income_account
            and line.display_type == 'tax'
        )

        self.assertFalse(discount_lines)
