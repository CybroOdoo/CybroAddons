# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestResConfigSettings(TransactionCase):
    """Tests for ResConfigSettings (advanced_vat_invoice)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.params = cls.env['ir.config_parameter'].sudo()

    def _new_settings(self, vals=None):
        return self.env['res.config.settings'].create(vals or {})

    def test_01_fields_exist(self):
        """generate_qr and is_qr fields must exist."""
        fields = self.env['res.config.settings']._fields
        self.assertIn('generate_qr', fields)
        self.assertIn('is_qr', fields)

    def test_02_selection_values(self):
        """generate_qr must have both selection options."""
        keys = [k for k, _ in self.env['res.config.settings']._fields['generate_qr'].selection]
        self.assertIn('automatically', keys)
        self.assertIn('manually', keys)

    def test_03_set_values_persists_params(self):
        """set_values writes generate_qr and is_qr to ir.config_parameter."""
        settings = self._new_settings({'generate_qr': 'automatically', 'is_qr': True})
        settings.set_values()
        self.assertEqual(self.params.get_param('advanced_vat_invoice.generate_qr'), 'automatically')
        self.assertTrue(self.params.get_param('advanced_vat_invoice.is_qr'))

    def test_04_get_values_reads_params(self):
        """get_values returns the stored params."""
        self.params.set_param('advanced_vat_invoice.generate_qr', 'manually')
        result = self._new_settings().get_values()
        self.assertEqual(result.get('generate_qr'), 'manually')

    def test_05_round_trip(self):
        """Values written by set_values are returned by get_values."""
        settings = self._new_settings({'generate_qr': 'manually', 'is_qr': True})
        settings.set_values()
        result = self._new_settings().get_values()
        self.assertEqual(result.get('generate_qr'), 'manually')
        self.assertTrue(result.get('is_qr'))
