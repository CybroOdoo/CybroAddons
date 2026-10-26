# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from unittest.mock import patch
from odoo.exceptions import UserError
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestCustomerProductQrcode(common.TransactionCase):
    """Test suite for customer_product_qrcode module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env['ir.config_parameter'].sudo().set_str(
            'customer_product_qr.config.customer_prefix', 'CUST-'
        )
        cls.env['ir.config_parameter'].sudo().set_str(
            'customer_product_qr.config.product_prefix', 'PROD-'
        )

    def _extract_report_data(self, action):
        """Helper to extract report data dictionary from an action dict."""
        if not action:
            return {}
        if 'data' in action and action['data']:
            return action['data']
        ctx = action.get('context', {})
        if isinstance(ctx, dict) and 'report_action' in ctx:
            return ctx['report_action'].get('data', {})
        return {}

    def test_01_res_config_settings(self):
        """Test retrieving and saving QR code prefix configuration settings."""
        settings = self.env['res.config.settings'].create({
            'customer_prefix': 'TEST-CUST-',
            'product_prefix': 'TEST-PROD-',
        })
        settings.set_values()
        cust_prefix = self.env['ir.config_parameter'].sudo().get_str(
            'customer_product_qr.config.customer_prefix'
        )
        prod_prefix = self.env['ir.config_parameter'].sudo().get_str(
            'customer_product_qr.config.product_prefix'
        )
        self.assertEqual(cust_prefix, 'TEST-CUST-')
        self.assertEqual(prod_prefix, 'TEST-PROD-')

        default_vals = self.env['res.config.settings'].default_get(
            ['customer_prefix', 'product_prefix']
        )
        self.assertEqual(default_vals.get('customer_prefix'), 'TEST-CUST-')
        self.assertEqual(default_vals.get('product_prefix'), 'TEST-PROD-')

        # Reset back for other tests
        self.env['ir.config_parameter'].sudo().set_str(
            'customer_product_qr.config.customer_prefix', 'CUST-'
        )
        self.env['ir.config_parameter'].sudo().set_str(
            'customer_product_qr.config.product_prefix', 'PROD-'
        )

    def test_02_partner_qrcode_and_sequence(self):
        """Test partner QR code and sequence generation."""
        partner = self.env['res.partner'].create({
            'name': 'Test Customer Partner',
            'email': 'customer@example.com',
        })
        self.assertTrue(partner.sequence)
        self.assertTrue(partner.sequence.startswith('CUST-'))
        self.assertTrue(partner.qr)

        # Test action_generate_qr
        report_action = partner.action_generate_qr()
        self.assertTrue(partner.qr)
        self.assertIn('type', report_action)

        # Test get_partner_by_qr
        found_partner_id = partner.get_partner_by_qr(sequence=partner.sequence)
        self.assertEqual(found_partner_id, partner.id)

        # Test generate_sequence alias
        partner.sequence = False
        partner.generate_sequence()
        self.assertTrue(partner.sequence)
        self.assertTrue(partner.sequence.startswith('CUST-'))

        # Test missing prefix behavior: create() does not raise UserError
        self.env['ir.config_parameter'].sudo().set_str(
            'customer_product_qr.config.customer_prefix', ''
        )
        partner_no_prefix = self.env['res.partner'].create({
            'name': 'No Prefix Partner',
        })
        self.assertFalse(partner_no_prefix.sequence)
        self.assertFalse(partner_no_prefix.qr)
        with self.assertRaises(UserError):
            partner_no_prefix.action_generate_sequence()
        with self.assertRaises(UserError):
            partner_no_prefix.action_generate_qr()

        # Restore prefix
        self.env['ir.config_parameter'].sudo().set_str(
            'customer_product_qr.config.customer_prefix', 'CUST-'
        )

        # Test multi-record action_generate_sequence and action_generate_qr
        partners = self.env['res.partner'].create([
            {'name': 'Multi Partner 1'},
            {'name': 'Multi Partner 2'},
        ])
        partners[0].sequence = False
        partners[1].sequence = False
        partners.action_generate_sequence()
        self.assertTrue(partners[0].sequence)
        self.assertTrue(partners[1].sequence)
        self.assertNotEqual(partners[0].sequence, partners[1].sequence)

        multi_action = partners.action_generate_qr()
        self.assertTrue(partners[0].qr)
        self.assertTrue(partners[1].qr)
        self.assertEqual(
            self._extract_report_data(multi_action).get('data'),
            partners.ids,
        )

        # Test action_generate_qr when sequence is empty
        partner.sequence = False
        partner.action_generate_qr()
        self.assertTrue(partner.sequence)

        # Test partner init method
        if 'customer_rank' in self.env['res.partner']._fields:
            cust_partner = self.env['res.partner'].create({
                'name': 'Init Partner',
                'customer_rank': 1,
                'sequence': 'TEMP',
            })
            cust_partner.sequence = False
            self.env['res.partner'].init()
            self.assertTrue(cust_partner.sequence)
            self.assertTrue(cust_partner.sequence.startswith('DEFINITPARTNER'))
        else:
            self.env['res.partner'].init()

        # Test action_generate_qr when qrcode is not available
        target_patch = (
            'odoo.addons.customer_product_qrcode.models.res_partner.qrcode'
        )
        with patch(target_patch, None):
            with self.assertRaises(UserError):
                partner.action_generate_qr()

    def test_03_product_qrcode_and_sequence(self):
        """Test product QR code and sequence generation."""
        product = self.env['product.product'].create({
            'name': 'Test QR Product',
            'list_price': 50.0,
        })
        self.assertIsInstance(product.sequence, int)
        self.assertTrue(product.qr_sequence)
        self.assertTrue(product.qr_sequence.startswith('PROD-'))
        self.assertTrue(product.qr)

        # Test action_generate_qr
        report_action = product.action_generate_qr()
        self.assertTrue(product.qr)
        self.assertIn('type', report_action)

        # Test get_product_by_qr
        found_product_id = product.get_product_by_qr(
            qr_sequence=product.qr_sequence
        )
        self.assertEqual(found_product_id, product.id)

        # Test generate_sequence alias
        product.qr_sequence = False
        product.generate_sequence()
        self.assertTrue(product.qr_sequence)
        self.assertTrue(product.qr_sequence.startswith('PROD-'))

        # Test missing prefix behavior: create() does not raise UserError
        self.env['ir.config_parameter'].sudo().set_str(
            'customer_product_qr.config.product_prefix', ''
        )
        product_no_prefix = self.env['product.product'].create({
            'name': 'No Prefix Product',
        })
        self.assertFalse(product_no_prefix.qr_sequence)
        self.assertFalse(product_no_prefix.qr)
        with self.assertRaises(UserError):
            product_no_prefix.action_generate_sequence()
        with self.assertRaises(UserError):
            product_no_prefix.action_generate_qr()

        # Restore prefix
        self.env['ir.config_parameter'].sudo().set_str(
            'customer_product_qr.config.product_prefix', 'PROD-'
        )

        # Test multi-record action_generate_sequence and action_generate_qr
        products = self.env['product.product'].create([
            {'name': 'Multi Product 1'},
            {'name': 'Multi Product 2'},
        ])
        products[0].qr_sequence = False
        products[1].qr_sequence = False
        products.action_generate_sequence()
        self.assertTrue(products[0].qr_sequence)
        self.assertTrue(products[1].qr_sequence)
        self.assertNotEqual(products[0].qr_sequence, products[1].qr_sequence)

        prod_multi_action = products.action_generate_qr()
        self.assertTrue(products[0].qr)
        self.assertTrue(products[1].qr)
        self.assertEqual(
            self._extract_report_data(prod_multi_action).get('data'),
            products.ids,
        )

        # Test action_generate_qr when sequence is empty
        product.qr_sequence = False
        product.action_generate_qr()
        self.assertTrue(product.qr_sequence)

        # Test action_generate_qr when qrcode is not available
        target_patch = (
            'odoo.addons.customer_product_qrcode.models.product_product.qrcode'
        )
        with patch(target_patch, None):
            with self.assertRaises(UserError):
                product.action_generate_qr()

    def test_04_product_template_generation(self):
        """Test generating QR codes from product template."""
        template = self.env['product.template'].create({
            'name': 'Template QR Product',
        })
        self.assertTrue(template.product_variant_ids)
        variant = template.product_variant_ids[0]
        variant.qr_sequence = False
        variant.qr = False

        template.action_generate_sequence()
        self.assertTrue(variant.qr_sequence)

        template.generate_sequence()
        self.assertTrue(variant.qr_sequence)

        report_action = template.action_generate_qr()
        self.assertTrue(variant.qr)
        self.assertIn('type', report_action)
        self.assertFalse(
            self.env['product.template'].browse().action_generate_qr()
        )

        # Multi-variant template test
        attr = self.env['product.attribute'].create({
            'name': 'Test Color Attribute',
            'value_ids': [
                (0, 0, {'name': 'Red'}),
                (0, 0, {'name': 'Blue'}),
            ],
        })
        template_multi = self.env['product.template'].create({
            'name': 'Multi Variant Template',
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': attr.id,
                    'value_ids': [(6, 0, attr.value_ids.ids)],
                }),
            ],
        })
        self.assertEqual(len(template_multi.product_variant_ids), 2)
        template_multi.product_variant_ids.write({
            'qr_sequence': False,
            'qr': False,
        })
        multi_qr_action = template_multi.action_generate_qr()
        for v in template_multi.product_variant_ids:
            self.assertTrue(v.qr_sequence)
            self.assertTrue(v.qr)
        self.assertEqual(
            self._extract_report_data(multi_qr_action).get('data'),
            template_multi.product_variant_ids.ids,
        )

    def test_05_report_and_server_actions(self):
        """Test report data fetching and server actions."""
        partner = self.env['res.partner'].create({'name': 'Report Partner'})
        product = self.env['product.product'].create({
            'name': 'Report Product',
        })

        report_model = self.env[
            'report.customer_product_qrcode.customer_qr_template'
        ]

        # Report values for partner
        res_partner_report = report_model._get_report_values(
            [partner.id],
            data={
                'type': 'cust',
                'data': partner.id,
                'context': {'active_model': 'res.partner'},
            }
        )
        self.assertIn('data', res_partner_report)
        self.assertEqual(res_partner_report['data'][0].id, partner.id)

        # Report values for product
        res_product_report = report_model._get_report_values(
            [product.id],
            data={
                'type': 'prod',
                'data': product.id,
                'context': {'active_model': 'product.product'},
            }
        )
        self.assertIn('data', res_product_report)
        self.assertEqual(res_product_report['data'][0].id, product.id)

        # Report values with list of IDs
        res_multi_report = report_model._get_report_values(
            [],
            data={
                'type': 'cust',
                'data': [partner.id],
            }
        )
        self.assertEqual(res_multi_report['data'][0].ids, [partner.id])

        # Report values for product template
        res_template_report = report_model._get_report_values(
            [product.product_tmpl_id.id],
            data={'context': {'active_model': 'product.template'}}
        )
        self.assertIn('data', res_template_report)

        # Server actions execution
        partner_action = self.env.ref(
            'customer_product_qrcode.generate_qr_partner_action'
        )
        partner.qr = False
        partner_action.with_context(
            active_ids=[partner.id], active_model='res.partner'
        ).run()
        self.assertTrue(partner.qr)

        product_action = self.env.ref(
            'customer_product_qrcode.generate_qr_product_action'
        )
        product.qr = False
        product_action.with_context(
            active_ids=[product.id], active_model='product.product'
        ).run()
        self.assertTrue(product.qr)
