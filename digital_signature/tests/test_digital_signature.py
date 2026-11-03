# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import base64
from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'digital_signature')
class TestDigitalSignature(TransactionCase):
    """Automated test cases for digital signature functionality across
    Purchase Orders, Account Moves, Stock Pickings, and Config Settings."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config_param = cls.env['ir.config_parameter'].sudo()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Signature Test Partner',
            'email': 'signature_test@example.com',
        })

        cls.product = cls.env['product.product'].create({
            'name': 'Signature Test Product',
            'type': 'consu',
            'list_price': 100.0,
            'standard_price': 60.0,
        })

        cls.dummy_sign = base64.b64encode(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00'
            b'\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r'
            b'\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        ).decode('ascii')

    def test_01_purchase_order_digital_signature(self):
        """Test purchase order signature fields and confirm validation."""
        self.config_param.set_bool(
            'digital_signature.is_confirm_sign_po', True
        )
        self.config_param.set_bool(
            'digital_signature.is_show_digital_sign_po', True
        )
        self.config_param.set_bool(
            'digital_signature.is_enable_options_po', True
        )

        po = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'product_qty': 2.0,
                    'price_unit': 60.0,
                }),
            ],
        })
        self.assertTrue(po.is_show_signature)
        self.assertTrue(po.is_enable_others)

        # Confirming without signature should raise UserError
        with self.assertRaises(UserError):
            po.button_confirm()

        # Add signature and confirm
        po.write({
            'digital_sign': self.dummy_sign,
            'sign_by': 'Purchasing Manager',
            'designation': 'Head of Procurement',
            'sign_on': fields.Datetime.now(),
        })
        po.button_confirm()
        self.assertEqual(po.state, 'purchase')

    def test_02_account_move_out_invoice_digital_signature(self):
        """Test customer invoice signature enforcement on action_post."""
        self.config_param.set_bool(
            'digital_signature.is_confirm_sign_invoice', True
        )
        self.config_param.set_bool(
            'digital_signature.is_show_digital_sign_invoice', True
        )
        self.config_param.set_bool(
            'digital_signature.is_enable_options_invoice', True
        )

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'quantity': 1.0,
                    'price_unit': 100.0,
                }),
            ],
        })
        self.assertTrue(invoice.is_show_signature)
        self.assertTrue(invoice.is_enable_others)

        # Posting without signature should raise UserError
        with self.assertRaises(UserError):
            invoice.action_post()

        # Add signature and post
        invoice.write({
            'digital_sign': self.dummy_sign,
            'sign_by': 'Accountant',
            'designation': 'Finance Lead',
            'sign_on': fields.Datetime.now(),
        })
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted')

    def test_03_account_move_in_invoice_digital_signature(self):
        """Test vendor bill signature enforcement on action_post."""
        self.config_param.set_bool(
            'digital_signature.is_confirm_sign_invoice', True
        )
        self.config_param.set_bool(
            'digital_signature.is_show_digital_sign_bill', True
        )

        bill = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'quantity': 1.0,
                    'price_unit': 50.0,
                }),
            ],
        })
        self.assertTrue(bill.is_show_sign_bill)

        # Posting without signature should raise UserError
        with self.assertRaises(UserError):
            bill.action_post()

        # Add signature and post
        bill.write({
            'digital_sign': self.dummy_sign,
            'sign_by': 'Auditor',
            'designation': 'Lead Auditor',
            'sign_on': fields.Datetime.now(),
        })
        bill.action_post()
        self.assertEqual(bill.state, 'posted')

    def test_04_stock_picking_digital_signature(self):
        """Test stock picking signature enforcement and compute methods."""
        self.config_param.set_bool(
            'digital_signature.is_confirm_sign_inventory', True
        )
        self.config_param.set_bool(
            'digital_signature.is_show_digital_sign_inventory', True
        )
        self.config_param.set_bool(
            'digital_signature.is_enable_options_inventory', True
        )
        self.config_param.set_str(
            'digital_signature.sign_applicable', 'both'
        )

        warehouse = self.env['stock.warehouse'].search([], limit=1)
        picking_type = warehouse.in_type_id

        picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
        })
        self.assertTrue(picking.is_show_sign)
        self.assertTrue(picking.is_enable_option)
        self.assertEqual(picking.sign_applicable, 'both')

        # Validating without signature should raise UserError
        with self.assertRaises(UserError):
            picking.button_validate()

        # Adding signature avoids UserError from signature check
        picking.write({
            'digital_sign': self.dummy_sign,
            'sign_by': 'Warehouse Supervisor',
            'designation': 'Logistics Manager',
            'sign_on': fields.Datetime.now(),
        })
        self.assertTrue(picking.digital_sign)

    def test_05_res_config_settings_persistence(self):
        """Test config settings saving and reading."""
        settings = self.env['res.config.settings'].create({
            'is_show_digital_sign_po': True,
            'is_enable_options_po': True,
            'is_confirm_sign_po': True,
            'is_show_digital_sign_inventory': True,
            'is_enable_options_inventory': True,
            'sign_applicable': 'delivery',
            'is_confirm_sign_inventory': True,
            'is_show_digital_sign_invoice': True,
            'is_enable_options_invoice': True,
            'is_confirm_sign_invoice': True,
            'is_show_digital_sign_bill': True,
        })
        settings.execute()

        self.assertEqual(
            self.config_param.get_str('digital_signature.sign_applicable'),
            'delivery',
        )
        self.assertTrue(
            self.config_param.get_bool(
                'digital_signature.is_show_digital_sign_po'
            )
        )
