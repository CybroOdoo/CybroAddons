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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestDirectSendEmail(TransactionCase):
    """Test suite for Direct Send Email module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Direct Send Test Partner',
            'email': 'direct_send_test@example.com',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Direct Send Test Product',
            'list_price': 100.0,
            'standard_price': 50.0,
            'type': 'consu',
        })

        # Create mail templates for sale, purchase, account
        cls.sale_template = cls.env['mail.template'].create({
            'name': 'Test Sale Template',
            'model_id': cls.env.ref('sale.model_sale_order').id,
            'subject': 'Sale Order {{ object.name }}',
            'body_html': '<p>Sale Order Test</p>',
        })
        cls.purchase_template = cls.env['mail.template'].create({
            'name': 'Test Purchase Template',
            'model_id': cls.env.ref('purchase.model_purchase_order').id,
            'subject': 'Purchase Order {{ object.name }}',
            'body_html': '<p>Purchase Order Test</p>',
        })
        cls.invoice_template = cls.env['mail.template'].create({
            'name': 'Test Invoice Template',
            'model_id': cls.env.ref('account.model_account_move').id,
            'subject': 'Invoice {{ object.name }}',
            'body_html': '<p>Invoice Test</p>',
        })

    def test_01_sale_direct_send(self):
        """Test sale order quotation and confirmed order direct send."""
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': 100.0,
                }),
            ],
        })

        icp = self.env['ir.config_parameter'].sudo()

        # 1. Setting disabled -> should raise ValidationError
        icp.set_bool('direct_send_email_template.is_direct_send_email_sale', False)
        with self.assertRaises(ValidationError):
            so.action_direct_send_sale()

        # 2. Setting enabled but template missing -> should raise ValidationError
        icp.set_bool('direct_send_email_template.is_direct_send_email_sale', True)
        icp.set_int('direct_send_email_template.direct_send_mailtemplate_sq', False)
        with self.assertRaises(ValidationError):
            so.action_direct_send_sale()

        # 3. Setting enabled and template set -> draft state
        icp.set_int(
            'direct_send_email_template.direct_send_mailtemplate_sq',
            self.sale_template.id,
        )
        with patch.object(type(so), 'message_post_with_source', return_value=True):
            so.action_direct_send_sale()
        self.assertTrue(so.direct_send_quo)

        # 4. Confirmed sale order state
        so.action_confirm()
        self.assertEqual(so.state, 'sale')

        # Template missing for confirmed SO
        icp.set_int('direct_send_email_template.direct_send_mailtemplate_so', False)
        with self.assertRaises(ValidationError):
            so.action_direct_send_sale()

        # Template configured for confirmed SO
        icp.set_int(
            'direct_send_email_template.direct_send_mailtemplate_so',
            self.sale_template.id,
        )
        with patch.object(type(so), 'message_post_with_source', return_value=True):
            so.action_direct_send_sale()
        self.assertTrue(so.direct_send_so)

    def test_02_purchase_direct_send(self):
        """Test purchase order RFQ and confirmed PO direct send."""
        po = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_qty': 2,
                    'price_unit': 50.0,
                }),
            ],
        })

        icp = self.env['ir.config_parameter'].sudo()

        # 1. Setting disabled -> should raise ValidationError
        icp.set_bool('direct_send_email_template.is_direct_send_email_purchase', False)
        with self.assertRaises(ValidationError):
            po.action_direct_send_purchase()

        # 2. Setting enabled but template missing
        icp.set_bool('direct_send_email_template.is_direct_send_email_purchase', True)
        icp.set_int('direct_send_email_template.direct_send_mailtemplate_prfq', False)
        with self.assertRaises(ValidationError):
            po.action_direct_send_purchase()

        # 3. Setting enabled and template configured for RFQ
        icp.set_int(
            'direct_send_email_template.direct_send_mailtemplate_prfq',
            self.purchase_template.id,
        )
        with patch.object(type(po), 'message_post_with_source', return_value=True):
            po.action_direct_send_purchase()
        self.assertTrue(po.direct_send_rfq)

        # 4. Confirmed purchase order state
        po.button_confirm()
        self.assertEqual(po.state, 'purchase')

        # Template missing for confirmed PO
        icp.set_int('direct_send_email_template.direct_send_mailtemplate_po', False)
        with self.assertRaises(ValidationError):
            po.action_direct_send_purchase()

        # Template configured for confirmed PO
        icp.set_int(
            'direct_send_email_template.direct_send_mailtemplate_po',
            self.purchase_template.id,
        )
        with patch.object(type(po), 'message_post_with_source', return_value=True):
            po.action_direct_send_purchase()
        self.assertTrue(po.direct_send_po)

    def test_03_account_move_direct_send(self):
        """Test account move out_invoice, out_refund, in_invoice, in_refund direct send."""
        icp = self.env['ir.config_parameter'].sudo()

        # Create Customer Invoice (out_invoice)
        inv = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'quantity': 1,
                    'price_unit': 100.0,
                }),
            ],
        })

        # 1. Setting disabled -> should raise ValidationError
        icp.set_bool('direct_send_email_template.is_direct_send_email_account', False)
        with self.assertRaises(ValidationError):
            inv.action_direct_send_account()

        # 2. Setting enabled but invoice not posted -> no-op / state != 'posted'
        icp.set_bool('direct_send_email_template.is_direct_send_email_account', True)
        icp.set_int(
            'direct_send_email_template.direct_send_mailtemplate_inv',
            self.invoice_template.id,
        )
        inv.action_direct_send_account()
        self.assertFalse(inv.direct_send_inv)

        # Post invoice
        inv.action_post()
        self.assertEqual(inv.state, 'posted')

        # Template missing
        icp.set_int('direct_send_email_template.direct_send_mailtemplate_inv', False)
        with self.assertRaises(ValidationError):
            inv.action_direct_send_account()

        # Template set
        icp.set_int(
            'direct_send_email_template.direct_send_mailtemplate_inv',
            self.invoice_template.id,
        )
        with patch.object(type(inv), 'message_post_with_source', return_value=True):
            inv.action_direct_send_account()
        self.assertTrue(inv.direct_send_inv)

        # Test out_refund (Credit Note)
        credit_note = self.env['account.move'].create({
            'move_type': 'out_refund',
            'partner_id': self.partner.id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'quantity': 1,
                    'price_unit': 100.0,
                }),
            ],
        })
        credit_note.action_post()

        # Template missing for credit note
        icp.set_int('direct_send_email_template.direct_send_mailtemplate_credit', False)
        with self.assertRaises(ValidationError):
            credit_note.action_direct_send_account()

        # Template set for credit note
        icp.set_int(
            'direct_send_email_template.direct_send_mailtemplate_credit',
            self.invoice_template.id,
        )
        with patch.object(type(credit_note), 'message_post_with_source', return_value=True):
            credit_note.action_direct_send_account()
        self.assertTrue(credit_note.direct_send_crd)

        # Test in_invoice (Vendor Bill)
        bill = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'quantity': 1,
                    'price_unit': 50.0,
                }),
            ],
        })
        bill.action_post()

        # Template missing for bill
        icp.set_int('direct_send_email_template.direct_send_mailtemplate_bill', False)
        with self.assertRaises(ValidationError):
            bill.action_direct_send_account()

        # Template set for bill
        icp.set_int(
            'direct_send_email_template.direct_send_mailtemplate_bill',
            self.invoice_template.id,
        )
        with patch.object(type(bill), 'message_post_with_source', return_value=True):
            bill.action_direct_send_account()
        self.assertTrue(bill.direct_send_bill)

        # Test in_refund (Vendor Refund)
        refund = self.env['account.move'].create({
            'move_type': 'in_refund',
            'partner_id': self.partner.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'quantity': 1,
                    'price_unit': 50.0,
                }),
            ],
        })
        refund.action_post()

        # Template missing for vendor refund
        icp.set_int('direct_send_email_template.direct_send_mailtemplate_refund', False)
        with self.assertRaises(ValidationError):
            refund.action_direct_send_account()

        # Template set for vendor refund
        icp.set_int(
            'direct_send_email_template.direct_send_mailtemplate_refund',
            self.invoice_template.id,
        )
        with patch.object(type(refund), 'message_post_with_source', return_value=True):
            refund.action_direct_send_account()
        self.assertTrue(refund.direct_send_ref)

    def test_04_res_config_settings(self):
        """Test res.config.settings direct send email parameters."""
        config = self.env['res.config.settings'].create({
            'is_direct_send_email_sale': True,
            'direct_send_mailtemplate_sq': self.sale_template.id,
            'direct_send_mailtemplate_so': self.sale_template.id,
            'is_direct_send_email_purchase': True,
            'direct_send_mailtemplate_prfq': self.purchase_template.id,
            'direct_send_mailtemplate_po': self.purchase_template.id,
            'is_direct_send_email_account': True,
            'direct_send_mailtemplate_inv': self.invoice_template.id,
            'direct_send_mailtemplate_credit': self.invoice_template.id,
            'direct_send_mailtemplate_bill': self.invoice_template.id,
            'direct_send_mailtemplate_refund': self.invoice_template.id,
        })
        config.execute()

        icp = self.env['ir.config_parameter'].sudo()
        self.assertTrue(
            icp.get_bool('direct_send_email_template.is_direct_send_email_sale'),
        )
        self.assertEqual(
            icp.get_int('direct_send_email_template.direct_send_mailtemplate_sq'),
            self.sale_template.id,
        )
        self.assertTrue(
            icp.get_bool('direct_send_email_template.is_direct_send_email_purchase'),
        )
        self.assertEqual(
            icp.get_int('direct_send_email_template.direct_send_mailtemplate_po'),
            self.purchase_template.id,
        )
        self.assertTrue(
            icp.get_bool('direct_send_email_template.is_direct_send_email_account'),
        )
        self.assertEqual(
            icp.get_int('direct_send_email_template.direct_send_mailtemplate_inv'),
            self.invoice_template.id,
        )
