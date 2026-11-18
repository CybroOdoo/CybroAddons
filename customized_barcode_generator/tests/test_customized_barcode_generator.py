# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCustomizedBarcodeGenerator(TransactionCase):
    """ Tests for the cost code computation and label values """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.env['ir.config_parameter'].sudo()
        cls.code = cls.env['barcode.code'].create({
            'name': 'Test Code',
            'code_for_zero': 'Z',
            'code_for_one': 'O',
            'code_for_two': 'T',
            'code_for_five': 'F',
            'active_check': True,
        })
        cls.product = cls.env['product.template'].create({
            'name': 'Labelled Product',
            'default_code': 'REF-001',
            'standard_price': 1250.75,
        })

    def _enable(self, standard_price=True, reference=False):
        self.config.set_bool(
            'customized_barcode_generator.require_standard_price',
            standard_price)
        self.config.set_bool(
            'customized_barcode_generator.require_ref', reference)
        self.product.invalidate_recordset(['cost_in_code'])

    def test_default_values(self):
        """ New rules get the default digit codes and a date """
        rule = self.env['barcode.code'].new({})
        self.assertEqual(rule.name, 'Numeric Code')
        self.assertEqual(rule.code_for_nine, 'j')
        self.assertTrue(rule.date_check)
        self.assertFalse(rule.active_check)

    def test_cost_in_code_enabled(self):
        """ The integer part of the cost is encoded with the active rule """
        self._enable()
        self.assertEqual(self.product.cost_in_code, 'OTFZ')

    def test_cost_in_code_setting_disabled(self):
        """ No code is computed when the setting is off """
        self._enable(standard_price=False)
        self.assertFalse(self.product.cost_in_code)

    def test_cost_in_code_without_active_rule(self):
        """ No code is computed when no rule is active """
        self._enable()
        self.code.active_check = False
        self.product.invalidate_recordset(['cost_in_code'])
        self.assertFalse(self.product.cost_in_code)

    def test_only_one_active_rule(self):
        """ A second active rule is refused """
        with self.assertRaises(ValidationError):
            self.env['barcode.code'].create({'active_check': True})
        other = self.env['barcode.code'].create({'active_check': False})
        with self.assertRaises(ValidationError):
            other.active_check = True

    def test_settings_fields(self):
        """ The settings store the configuration parameters """
        self.env['res.config.settings'].create({
            'require_standard_price': True,
            'require_ref': True,
        }).execute()
        self.assertTrue(self.config.get_bool(
            'customized_barcode_generator.require_standard_price'))
        self.assertTrue(self.config.get_bool(
            'customized_barcode_generator.require_ref'))

    def test_label_values(self):
        """ The label wizard passes the cost code and optional reference """
        wizard = self.env['product.label.layout'].create({
            'product_tmpl_ids': [(6, 0, self.product.ids)],
        })
        variant = self.product.product_variant_id
        self._enable(reference=False)
        values = wizard._prepare_label_values(variant, 'REF-001', 1, False)
        self.assertEqual(values['cost_in_code'], 'OTFZ')
        self.assertEqual(values['cost_code_reference'], '')
        self._enable(reference=True)
        values = wizard._prepare_label_values(
            self.product, 'REF-001', 1, False)
        self.assertEqual(values['cost_in_code'], 'OTFZ')
        self.assertEqual(values['cost_code_reference'], 'REF-001')

    def test_label_report_renders(self):
        """ The 2 x 7 label report renders the cost code """
        self._enable(reference=True)
        wizard = self.env['product.label.layout'].create({
            'product_tmpl_ids': [(6, 0, self.product.ids)],
            'print_format': '2x7',
        })
        xml_id, data = wizard._prepare_report_data()
        html = self.env['ir.actions.report']._render_qweb_html(
            xml_id, self.product.ids, data=data)[0].decode()
        self.assertRegex(html, r'(?s)o_label_cost_code.*?REF-001.*?OTFZ')
