# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Unit tests for the dynamic.action wizard model."""

from odoo.exceptions import ValidationError
from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install')
class TestDynamicAction(TransactionCase):
    """Test cases for each function in dynamic.action model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        # Ensure income and receivable accounts exist
        cls.revenue_account = cls.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_ids', 'in', cls.company.id),
        ], limit=1)
        if not cls.revenue_account:
            cls.revenue_account = cls.env['account.account'].create({
                'name': 'Sales Revenue',
                'code': '400000',
                'account_type': 'income',
                'company_ids': [(6, 0, [cls.company.id])],
            })

        cls.receivable_account = cls.env['account.account'].search([
            ('account_type', '=', 'asset_receivable'),
            ('company_ids', 'in', cls.company.id),
        ], limit=1)
        if not cls.receivable_account:
            cls.receivable_account = cls.env['account.account'].create({
                'name': 'Account Receivable',
                'code': '120000',
                'account_type': 'asset_receivable',
                'reconcile': True,
                'company_ids': [(6, 0, [cls.company.id])],
            })

        # Ensure a sale journal exists for customer invoices
        cls.sale_journal = cls.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', cls.company.id),
        ], limit=1)
        if not cls.sale_journal:
            cls.sale_journal = cls.env['account.journal'].create({
                'name': 'Customer Invoices',
                'code': 'INV',
                'type': 'sale',
                'company_id': cls.company.id,
                'default_account_id': cls.revenue_account.id,
            })

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Dynamic Partner',
            'email': 'dynamic_test@example.com',
            'property_account_receivable_id': cls.receivable_account.id,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Dynamic Product',
            'type': 'consu',
            'list_price': 100.0,
        })

        # 1. Sale Order
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': cls.product.id,
                    'product_uom_qty': 2.0,
                    'price_unit': 100.0,
                }),
            ],
        })

        # 2. Purchase Order
        cls.purchase_order = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': cls.product.id,
                    'product_qty': 5.0,
                    'price_unit': 80.0,
                }),
            ],
        })

        # 3. Stock Picking
        cls.warehouse = cls.env['stock.warehouse'].search([], limit=1)
        cls.picking_type = cls.env['stock.picking.type'].search([
            ('warehouse_id', '=', cls.warehouse.id),
            ('code', '=', 'outgoing'),
        ], limit=1)
        cls.picking = cls.env['stock.picking'].create({
            'picking_type_id': cls.picking_type.id,
            'location_id': cls.picking_type.default_location_src_id.id,
            'location_dest_id': cls.picking_type.default_location_dest_id.id,
            'partner_id': cls.partner.id,
        })

        # 4. Customer Invoice (out_invoice)
        cls.invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'journal_id': cls.sale_journal.id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': cls.product.id,
                    'quantity': 1.0,
                    'price_unit': 100.0,
                    'account_id': cls.revenue_account.id,
                }),
            ],
        })

        # 5. Journal Entry (entry) - for validation error test
        cls.entry = cls.env['account.move'].create({
            'move_type': 'entry',
            'partner_id': cls.partner.id,
            'journal_id': cls.sale_journal.id,
        })

    def test__selection_target_model(self):
        """Test _selection_target_model returns the expected supported models."""
        selection = self.env['dynamic.action']._selection_target_model()
        model_names = [item[0] for item in selection]
        self.assertIn('sale.order', model_names)
        self.assertIn('purchase.order', model_names)
        self.assertIn('stock.picking', model_names)
        self.assertIn('account.move', model_names)

    def test__set_resource_ref(self):
        """Test _set_resource_ref sets res_id and res_model from resource_ref."""
        wizard = self.env['dynamic.action'].create({
            'resource_ref': f"sale.order,{self.sale_order.id}",
        })
        self.assertEqual(wizard.res_id, self.sale_order.id)
        self.assertEqual(wizard.res_model, 'sale.order')

    def test__validate_record(self):
        """Test _validate_record success and validation error conditions."""
        # Valid sale order
        wizard_sale = self.env['dynamic.action'].create({
            'resource_ref': f"sale.order,{self.sale_order.id}",
        })
        validated = wizard_sale._validate_record()
        self.assertEqual(validated, self.sale_order)

        # Empty record validation error
        wizard_empty = self.env['dynamic.action'].create({})
        with self.assertRaises(ValidationError):
            wizard_empty._validate_record()

        # Non-existing record validation error
        wizard_missing = self.env['dynamic.action'].create({
            'res_model': 'sale.order',
            'res_id': 99999999,
        })
        with self.assertRaises(ValidationError):
            wizard_missing._validate_record()

        # Entry move_type validation error
        wizard_entry = self.env['dynamic.action'].create({
            'resource_ref': f"account.move,{self.entry.id}",
        })
        with self.assertRaises(ValidationError):
            wizard_entry._validate_record()

    def test_action_print_report(self):
        """Test action_print_report returns report action for supported models."""
        for record in [self.sale_order, self.purchase_order, self.picking, self.invoice]:
            wizard = self.env['dynamic.action'].create({
                'resource_ref': f"{record._name},{record.id}",
            })
            action = wizard.action_print_report()
            self.assertIsInstance(action, dict)
            self.assertIn(action.get('type'), ['ir.actions.report', 'ir.actions.act_window'])

    def test_action_download_report(self):
        """Test action_download_report generates attachment and returns download act_url."""
        wizard = self.env['dynamic.action'].create({
            'resource_ref': f"sale.order,{self.sale_order.id}",
        })
        res = wizard.action_download_report()
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get('type'), 'ir.actions.act_url')
        self.assertIn('download=true', res.get('url', ''))

        # Check attachment created
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', self.sale_order.id),
        ], limit=1)
        self.assertTrue(attachment)
        self.assertEqual(attachment.mimetype, 'application/pdf')

    def test_action_open_report(self):
        """Test action_open_report returns URL action to open report in new tab."""
        wizard = self.env['dynamic.action'].create({
            'resource_ref': f"purchase.order,{self.purchase_order.id}",
        })
        res = wizard.action_open_report()
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get('type'), 'ir.actions.act_url')
        self.assertEqual(res.get('target'), 'new')
        self.assertIn(f"/report/pdf/purchase.report_purchaseorder/{self.purchase_order.id}", res.get('url', ''))

    def test_action_share_email(self):
        """Test action_share_email for sale order, purchase order, invoice, and unshared models."""
        # 1. Sale Order draft vs confirmed
        wizard_so = self.env['dynamic.action'].create({
            'resource_ref': f"sale.order,{self.sale_order.id}",
        })
        act_so = wizard_so.action_share_email()
        self.assertEqual(act_so.get('res_model'), 'mail.compose.message')
        self.assertEqual(act_so.get('context', {}).get('default_template_id'),
                         self.env.ref('sale.email_template_edi_sale').id)

        self.sale_order.action_confirm()
        act_so_confirmed = wizard_so.action_share_email()
        self.assertEqual(act_so_confirmed.get('context', {}).get('default_template_id'),
                         self.env.ref('sale.mail_template_sale_confirmation').id)

        # 2. Purchase Order draft vs confirmed
        wizard_po = self.env['dynamic.action'].create({
            'resource_ref': f"purchase.order,{self.purchase_order.id}",
        })
        act_po = wizard_po.action_share_email()
        self.assertEqual(act_po.get('context', {}).get('default_template_id'),
                         self.env.ref('purchase.email_template_edi_purchase').id)

        self.purchase_order.button_confirm()
        act_po_confirmed = wizard_po.action_share_email()
        self.assertEqual(act_po_confirmed.get('context', {}).get('default_template_id'),
                         self.env.ref('purchase.email_template_edi_purchase_done').id)

        # 3. Account Move (out_invoice vs out_refund)
        wizard_inv = self.env['dynamic.action'].create({
            'resource_ref': f"account.move,{self.invoice.id}",
        })
        act_inv = wizard_inv.action_share_email()
        self.assertEqual(act_inv.get('context', {}).get('default_template_id'),
                         self.env.ref('account.email_template_edi_invoice').id)

        refund = self.env['account.move'].create({
            'move_type': 'out_refund',
            'partner_id': self.partner.id,
            'journal_id': self.sale_journal.id,
        })
        wizard_refund = self.env['dynamic.action'].create({
            'resource_ref': f"account.move,{refund.id}",
        })
        act_refund = wizard_refund.action_share_email()
        self.assertEqual(act_refund.get('context', {}).get('default_template_id'),
                         self.env.ref('account.email_template_edi_credit_note').id)

        # 4. Stock Picking (no share option -> raises ValidationError)
        wizard_pick = self.env['dynamic.action'].create({
            'resource_ref': f"stock.picking,{self.picking.id}",
        })
        with self.assertRaises(ValidationError):
            wizard_pick.action_share_email()
