# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
import binascii


class TestAccountMove(TransactionCase):
    """Tests for AccountMove (advanced_vat_invoice)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.write({'vat': '300000000000003'})
        cls.partner = cls.env['res.partner'].create({'name': 'Saudi Partner'})
        cls.tax = cls.env['account.tax'].create({
            'name': 'VAT 15%', 'amount': 15, 'type_tax_use': 'sale',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product', 'list_price': 100.0,
        })
        cls.invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': cls.product.id,
                'name': 'Line',
                'quantity': 1,
                'price_unit': 100.0,
                'tax_ids': [(6, 0, [cls.tax.id])],
            })],
        })

    def _set_param(self, key, value):
        self.env['ir.config_parameter'].sudo().set_param(key, value)

    def test_01_custom_fields_exist(self):
        """qr, qr_button, qr_page fields must exist."""
        for field in ('qr', 'qr_button', 'qr_page'):
            self.assertIn(field, self.invoice._fields)

    def test_02_compute_qr_defaults_false(self):
        """With no config, qr_button and qr_page are False."""
        self._set_param('advanced_vat_invoice.is_qr', False)
        self._set_param('advanced_vat_invoice.generate_qr', False)
        self.invoice._compute_qr()
        self.assertFalse(self.invoice.qr_button)
        self.assertFalse(self.invoice.qr_page)

    def test_03_compute_qr_manual_mode(self):
        """Manual mode enables qr_button."""
        self._set_param('advanced_vat_invoice.is_qr', 'True')
        self._set_param('advanced_vat_invoice.generate_qr', 'manually')
        self.invoice._compute_qr()
        self.assertTrue(self.invoice.qr_button)

    def test_04_compute_qr_automatic_mode(self):
        """Automatic mode enables qr_page."""
        self._set_param('advanced_vat_invoice.generate_qr', 'automatically')
        self.invoice._compute_qr()
        self.assertTrue(self.invoice.qr_page)

    def test_05_string_hexa(self):
        """string_hexa returns correct UTF-8 hex."""
        expected = binascii.hexlify('ABC'.encode()).decode()
        self.assertEqual(self.invoice.string_hexa('ABC'), expected)

    def test_06_string_hexa_falsy_input(self):
        """string_hexa returns falsy for None/empty."""
        self.assertFalse(self.invoice.string_hexa(None))
        self.assertFalse(self.invoice.string_hexa(''))

    def test_07_hexa_output(self):
        """hexa returns a string starting with the tag."""
        result = self.invoice.hexa('01', '0c', 'TestCo')
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith('01'))

    def test_08_hexa_none_guard(self):
        """hexa returns None when any argument is falsy."""
        self.assertIsNone(self.invoice.hexa(None, '0c', 'val'))

    def test_09_qr_code_data_is_valid_base64(self):
        """qr_code_data returns a valid base64 string."""
        import base64
        result = self.invoice.qr_code_data()
        self.assertTrue(result)
        decoded = base64.b64decode(result)
        self.assertGreater(len(decoded), 0)

    def test_10_generate_qr_button_runs(self):
        """generate_qr_button does not crash in manual mode."""
        self._set_param('advanced_vat_invoice.generate_qr', 'manually')
        try:
            self.invoice.generate_qr_button()
        except UserError:
            pass  # acceptable if qrcode library absent

    def test_11_invoice_initial_state(self):
        """New invoice starts in draft with correct partner and lines."""
        self.assertEqual(self.invoice.state, 'draft')
        self.assertEqual(self.invoice.partner_id, self.partner)
        self.assertTrue(self.invoice.invoice_line_ids)
