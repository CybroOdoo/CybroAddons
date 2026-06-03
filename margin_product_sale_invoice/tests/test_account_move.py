# -*- coding: utf-8 -*-

from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


class _MarginProductSaleInvoiceInvoiceCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.currency = cls.company.currency_id
        cls.partner = cls.env['res.partner'].create({
            'name': 'Margin Test Customer',
        })
        cls.income_account = cls.env['account.account'].search([
            ('company_id', '=', cls.company.id),
            ('account_type', '=', 'income'),
        ], limit=1)
        if not cls.income_account:
            cls.income_account = cls.env['account.account'].create({
                'name': 'Margin Test Income',
                'code': 'MARGINC',
                'account_type': 'income',
                'company_id': cls.company.id,
                'reconcile': False,
            })
        cls.sale_journal = cls.env['account.journal'].search([
            ('company_id', '=', cls.company.id),
            ('type', '=', 'sale'),
        ], limit=1)
        if not cls.sale_journal:
            cls.sale_journal = cls.env['account.journal'].create({
                'name': 'Margin Test Sales Journal',
                'code': 'MTSJ',
                'type': 'sale',
                'company_id': cls.company.id,
                'default_account_id': cls.income_account.id,
            })
        cls.positive_template = cls.env['product.template'].create({
            'name': 'Margin Positive Product',
            'list_price': 200.0,
            'standard_price': 80.0,
        })
        cls.zero_template = cls.env['product.template'].create({
            'name': 'Margin Zero Price Product',
            'list_price': 0.0,
            'standard_price': 80.0,
        })
        cls.positive_variant = cls.positive_template.product_variant_id
        cls.zero_variant = cls.zero_template.product_variant_id
        cls.invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'journal_id': cls.sale_journal.id,
            'invoice_line_ids': [
                Command.create({
                    'name': 'Margin Invoice Line',
                    'product_id': cls.positive_variant.id,
                    'quantity': 2.0,
                    'price_unit': 200.0,
                    'account_id': cls.income_account.id,
                }),
            ],
        })
        cls.invoice_zero = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'journal_id': cls.sale_journal.id,
            'invoice_line_ids': [
                Command.create({
                    'name': 'Zero Margin Invoice Line',
                    'quantity': 1.0,
                    'price_unit': 0.0,
                    'account_id': cls.income_account.id,
                }),
            ],
        })


@tagged('-at_install', 'post_install')
class TestAccountMoveMargin(_MarginProductSaleInvoiceInvoiceCommon):

    def test_compute_cost_price_and_margin_amount(self):
        line = self.invoice.invoice_line_ids[0]

        self.assertAlmostEqual(line.cost_price_amount, 80.0)
        self.assertAlmostEqual(line.margin_amount, 240.0)
        self.assertAlmostEqual(self.invoice.margin_amount_total, 240.0)
        self.assertAlmostEqual(
            self.invoice.margin_percent_amount,
            self.invoice.margin_amount_total / self.invoice.amount_total,
        )

    def test_zero_value_line_and_invoice_margin(self):
        line = self.invoice_zero.invoice_line_ids[0]

        self.assertEqual(line.cost_price_amount, 0.0)
        self.assertEqual(line.margin_amount, 0.0)
        self.assertEqual(self.invoice_zero.margin_amount_total, 0.0)
        self.assertEqual(self.invoice_zero.margin_percent_amount, 0.0)
