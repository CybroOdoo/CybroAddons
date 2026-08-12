# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestBomComparison(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create components (products)
        cls.component_a = cls.env['product.product'].create({
            'name': 'Component A',
            'type': 'consu',
            'standard_price': 10.0,
            'lst_price': 15.0,
        })
        cls.component_b = cls.env['product.product'].create({
            'name': 'Component B',
            'type': 'consu',
            'standard_price': 20.0,
            'lst_price': 30.0,
        })

        # Create product template for the main product
        cls.product_tmpl = cls.env['product.template'].create({
            'name': 'Finished Product',
            'type': 'consu',
        })

        # Create two BOMs for the main product
        cls.bom_1 = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.product_tmpl.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {
                    'product_id': cls.component_a.id,
                    'product_qty': 2.0,
                }),
                (0, 0, {
                    'product_id': cls.component_b.id,
                    'product_qty': 1.0,
                }),
            ]
        })
        # BoM 1 cost = 2 * 10 + 1 * 20 = 40.0
        # BoM 1 sales price = 2 * 15 + 1 * 30 = 60.0

        cls.bom_2 = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.product_tmpl.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {
                    'product_id': cls.component_a.id,
                    'product_qty': 1.0,
                }),
                (0, 0, {
                    'product_id': cls.component_b.id,
                    'product_qty': 2.0,
                }),
            ]
        })
        # BoM 2 cost = 1 * 10 + 2 * 20 = 50.0
        # BoM 2 sales price = 1 * 15 + 2 * 30 = 75.0

    def test_wizard_defaults_and_computes(self):
        """Test default values and computed fields of the wizard"""
        # Create wizard with product_tmpl
        wizard = self.env['bom.comparison'].create({
            'product_tmpl_id': self.product_tmpl.id,
            'analysis': 'cost',
        })

        # Check default value
        self.assertEqual(wizard.product_unit, 1)

        # Check all_bom_ids is computed correctly
        self.assertEqual(set(wizard.all_bom_ids.ids), {self.bom_1.id, self.bom_2.id})

    def test_wizard_validation_constraint(self):
        """Test that ValidationError is raised if less than two BOMs are selected"""
        # Case 1: 0 BOMs selected
        with self.assertRaises(ValidationError):
            self.env['bom.comparison'].create({
                'product_tmpl_id': self.product_tmpl.id,
                'bom_ids': [(6, 0, [])],
                'analysis': 'cost',
            })

        # Case 2: 1 BOM selected
        with self.assertRaises(ValidationError):
            self.env['bom.comparison'].create({
                'product_tmpl_id': self.product_tmpl.id,
                'bom_ids': [(6, 0, [self.bom_1.id])],
                'analysis': 'cost',
            })

        # Case 3: 2 BOMs selected (valid case)
        wizard = self.env['bom.comparison'].create({
            'product_tmpl_id': self.product_tmpl.id,
            'bom_ids': [(6, 0, [self.bom_1.id, self.bom_2.id])],
            'analysis': 'cost',
        })
        self.assertEqual(len(wizard.bom_ids), 2)

    def test_wizard_onchange(self):
        """Test onchange method that clears bom_ids when product changes"""
        wizard = self.env['bom.comparison'].create({
            'product_tmpl_id': self.product_tmpl.id,
            'bom_ids': [(6, 0, [self.bom_1.id, self.bom_2.id])],
            'analysis': 'cost',
        })

        # Trigger onchange
        wizard._onchange_product_tmpl_id()
        self.assertFalse(wizard.bom_ids)

    def test_wizard_action_comparison_report(self):
        """Test report action method returns correct action"""
        wizard = self.env['bom.comparison'].create({
            'product_tmpl_id': self.product_tmpl.id,
            'bom_ids': [(6, 0, [self.bom_1.id, self.bom_2.id])],
            'analysis': 'cost',
        })
        action = wizard.action_comparison_report()
        self.assertEqual(action['report_name'], 'bom_comparison_report.bom_compare_report')
        self.assertEqual(action['data']['form_data']['id'], wizard.id)

    def test_report_values_cost_analysis(self):
        """Test report data generation with cost analysis"""
        wizard = self.env['bom.comparison'].create({
            'product_tmpl_id': self.product_tmpl.id,
            'bom_ids': [(6, 0, [self.bom_1.id, self.bom_2.id])],
            'analysis': 'cost',
            'product_unit': 5,
        })

        report_model = self.env['report.bom_comparison_report.bom_compare_report']
        report_data = report_model._get_report_values(docids=[], data={'form_data': wizard.read()[0]})

        # Verify the doc_model and other returned dict values
        self.assertEqual(report_data['doc_model'], 'bom.compare.wizard')
        data = report_data['data']
        self.assertEqual(data['analysis'], 'cost')
        self.assertEqual(data['unit'], 5)

        bom_reports = data['bom_report']
        self.assertEqual(len(bom_reports), 2)

        # Locate bom_1 and bom_2 reports
        report_bom_1 = next(r for r in bom_reports if r['bom_name'] == self.bom_1.display_name)
        report_bom_2 = next(r for r in bom_reports if r['bom_name'] == self.bom_2.display_name)

        # bom_1: 2 * 10 + 1 * 20 = 40.0
        self.assertEqual(report_bom_1['products'], 2)
        self.assertEqual(report_bom_1['total'], 40.0)
        self.assertEqual(report_bom_1['total_given'], 200.0)

        # bom_2: 1 * 10 + 2 * 20 = 50.0
        self.assertEqual(report_bom_2['products'], 2)
        self.assertEqual(report_bom_2['total'], 50.0)
        self.assertEqual(report_bom_2['total_given'], 250.0)

        # bom_1 is cheaper (200.0 vs 250.0), so better option should be bom_1
        self.assertEqual(data['better_option']['bom_name'], self.bom_1.display_name)

    def test_report_values_sale_price_analysis(self):
        """Test report data generation with sale price analysis"""
        wizard = self.env['bom.comparison'].create({
            'product_tmpl_id': self.product_tmpl.id,
            'bom_ids': [(6, 0, [self.bom_1.id, self.bom_2.id])],
            'analysis': 'sale_price',
            'product_unit': 2,
        })

        report_model = self.env['report.bom_comparison_report.bom_compare_report']
        report_data = report_model._get_report_values(docids=[], data={'form_data': wizard.read()[0]})

        data = report_data['data']
        self.assertEqual(data['analysis'], 'sale_price')
        self.assertEqual(data['unit'], 2)

        bom_reports = data['bom_report']
        report_bom_1 = next(r for r in bom_reports if r['bom_name'] == self.bom_1.display_name)
        report_bom_2 = next(r for r in bom_reports if r['bom_name'] == self.bom_2.display_name)

        # bom_1: 2 * 15 + 1 * 30 = 60.0
        self.assertEqual(report_bom_1['total'], 60.0)
        self.assertEqual(report_bom_1['total_given'], 120.0)

        # bom_2: 1 * 15 + 2 * 30 = 75.0
        self.assertEqual(report_bom_2['total'], 75.0)
        self.assertEqual(report_bom_2['total_given'], 150.0)

        # bom_1 is cheaper (120.0 vs 150.0), so better option should be bom_1
        self.assertEqual(data['better_option']['bom_name'], self.bom_1.display_name)

    def test_report_values_division_by_zero_handling(self):
        """Test that a BoM with product_qty = 0 does not raise division by zero error"""
        bom_zero = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_tmpl.id,
            'product_qty': 0.0,
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {
                    'product_id': self.component_a.id,
                    'product_qty': 1.0,
                }),
            ]
        })

        wizard = self.env['bom.comparison'].create({
            'product_tmpl_id': self.product_tmpl.id,
            'bom_ids': [(6, 0, [self.bom_1.id, bom_zero.id])],
            'analysis': 'cost',
            'product_unit': 1,
        })

        report_model = self.env['report.bom_comparison_report.bom_compare_report']
        # This call should not raise ZeroDivisionError and should complete successfully
        report_data = report_model._get_report_values(docids=[], data={'form_data': wizard.read()[0]})

        bom_reports = report_data['data']['bom_report']
        report_bom_zero = next(r for r in bom_reports if r['bom_name'] == bom_zero.display_name)

        # Since bom_zero.product_qty is 0, the unit_total is set to 0
        self.assertEqual(report_bom_zero['total'], 0.0)
        self.assertEqual(report_bom_zero['total_given'], 0.0)
        # bom_zero should be the better option since its cost is 0
        self.assertEqual(report_data['data']['better_option']['bom_name'], bom_zero.display_name)
