###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
"""Unit tests for product_profit_report module."""
from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'product_profit_report')
class TestProductProfitReport(TransactionCase):
    """Test suite for product profit report wizard, models and reports."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Profit Customer',
        })

        # Category hierarchy
        cls.category_parent = cls.env['product.category'].create({
            'name': 'Electronics Parent',
        })
        cls.category_child = cls.env['product.category'].create({
            'name': 'Smartphones Child',
            'parent_id': cls.category_parent.id,
        })

        # Products
        cls.product_a = cls.env['product.product'].create({
            'name': 'Flagship Smartphone',
            'categ_id': cls.category_child.id,
            'standard_price': 50.0,
            'list_price': 100.0,
        })
        cls.product_b = cls.env['product.product'].create({
            'name': 'Budget Smartphone',
            'categ_id': cls.category_child.id,
            'standard_price': 30.0,
            'list_price': 60.0,
        })
        cls.product_c = cls.env['product.product'].create({
            'name': 'Premium Tablet',
            'categ_id': cls.category_child.id,
            'standard_price': 100.0,
            'list_price': 200.0,
        })

        # Price history
        cls.price_history_a = cls.env['price.history'].create({
            'company_id': cls.company.id,
            'product_id': cls.product_a.id,
            'cost': 45.0,
            'datetime': fields.Datetime.now() - timedelta(days=2),
        })

        # Invoices
        cls.invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'invoice_date': fields.Date.today() - timedelta(days=1),
            'invoice_line_ids': [
                fields.Command.create({
                    'product_id': cls.product_a.id,
                    'quantity': 10,
                    'price_unit': 100.0,
                    'discount': 10.0,
                }),
                fields.Command.create({
                    'product_id': cls.product_b.id,
                    'quantity': 5,
                    'price_unit': 60.0,
                    'discount': 0.0,
                }),
                fields.Command.create({
                    'product_id': cls.product_c.id,
                    'quantity': 2,
                    'price_unit': 200.0,
                    'discount': 20.0,
                }),
            ],
        })
        cls.invoice.action_post()

        # Credit note / Refund
        cls.refund = cls.env['account.move'].create({
            'move_type': 'out_refund',
            'partner_id': cls.partner.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [
                fields.Command.create({
                    'product_id': cls.product_a.id,
                    'quantity': 2,
                    'price_unit': 100.0,
                    'discount': 0.0,
                }),
            ],
        })
        cls.refund.action_post()

    def test_01_price_history_and_product_get_history_price(self):
        """Test historical price lookup on product.product."""
        # Current price history cost is 45.0
        hist_cost = self.product_a.get_history_price(
            self.company.id,
            date=fields.Datetime.now(),
        )
        self.assertEqual(hist_cost, 45.0)

        # Before any price history existed, returns 0.0
        past_date = fields.Datetime.now() - timedelta(days=10)
        past_cost = self.product_a.get_history_price(
            self.company.id,
            date=past_date,
        )
        self.assertEqual(past_cost, 0.0)

        # Default company on price.history
        self.assertEqual(
            self.price_history_a.company_id,
            self.company,
        )
        hist_default = self.env['price.history'].create({
            'product_id': self.product_b.id,
            'cost': 25.0,
        })
        self.assertEqual(hist_default.company_id, self.company)

    def test_02_profit_product_wizard_category_onchange(self):
        """Test wizard category selection and child category resolution."""
        wizard = self.env['profit.product'].create({
            'company_id': self.company.id,
            'categ_id': self.category_parent.id,
        })
        self.assertTrue(wizard.from_date)
        self.assertTrue(wizard.to_date)

        # Trigger onchange
        wizard._onchange_categ_id()
        self.assertIn(self.product_a, wizard.product_product_ids)
        self.assertIn(self.product_b, wizard.product_product_ids)

        # Test recursive child categories
        child_ids = wizard.get_all_child_categories(self.category_parent)
        self.assertIn(self.category_child.id, child_ids)

        # Clear category
        wizard.categ_id = False
        wizard._onchange_categ_id()
        self.assertFalse(wizard.product_product_ids)

    def test_03_wizard_action_print_pdf_report(self):
        """Test wizard report printing action."""
        wizard = self.env['profit.product'].create({
            'company_id': self.company.id,
            'categ_id': self.category_parent.id,
            'from_date': fields.Date.today() - timedelta(days=30),
            'to_date': fields.Date.today() + timedelta(days=1),
        })
        wizard._onchange_categ_id()
        action = wizard.action_print_pdf_report()
        ctx_report = action.get('context', {}).get('report_action')
        report_action = ctx_report or action
        self.assertEqual(report_action.get('type'), 'ir.actions.report')
        self.assertEqual(
            report_action.get('report_name'),
            'product_profit_report.product_profit_report',
        )

    def test_04_report_values_generation(self):
        """Test report data calculation for invoices and refunds."""
        wizard = self.env['profit.product'].create({
            'company_id': self.company.id,
            'categ_id': self.category_parent.id,
            'from_date': fields.Date.today() - timedelta(days=30),
            'to_date': fields.Date.today() + timedelta(days=1),
        })
        wizard._onchange_categ_id()

        report_model = self.env[
            'report.product_profit_report.product_profit_report'
        ]
        data = {'form': wizard.read([])[0]}
        res = report_model._get_report_values([], data)

        self.assertIn('groups', res)
        self.assertIn('report_date', res)
        groups = res['groups']

        # Product A: invoice (10 qty @ 90 sale = 900, expense 10 * 45 = 450)
        # refund (-2 qty @ 100 sale = -200, expense -2 * 45 = -90)
        # Net qty: 8, net sales: 700, net expense: 360, net profit: 340
        self.assertIn(self.product_a.id, groups)
        prod_a_stats = groups[self.product_a.id]
        self.assertEqual(prod_a_stats['qty'], 8)
        self.assertAlmostEqual(prod_a_stats['sales'], 700.0)
        self.assertAlmostEqual(prod_a_stats['expense'], 360.0)
        self.assertAlmostEqual(prod_a_stats['profit'], 340.0)

        # Product B: 5 qty @ 60 = 300, expense = 5 * standard_price (30) = 150
        # (expense history was 0 so standard_price is used)
        self.assertIn(self.product_b.id, groups)
        prod_b_stats = groups[self.product_b.id]
        self.assertEqual(prod_b_stats['qty'], 5)
        self.assertAlmostEqual(prod_b_stats['sales'], 300.0)
        self.assertAlmostEqual(prod_b_stats['expense'], 150.0)
        self.assertAlmostEqual(prod_b_stats['profit'], 150.0)

        # Product C (unmasked discount test): 2 qty @ 200 with 20% discount
        # Correct: 2 * (200 * (1 - 0.20)) = 320.0
        # If buggy (price_unit - discount): 2 * (200 - 20) = 360.0
        # Expense: 2 * 100.0 (standard_price fallback) = 200.0, Profit: 120.0
        self.assertIn(self.product_c.id, groups)
        prod_c_stats = groups[self.product_c.id]
        self.assertEqual(prod_c_stats['qty'], 2)
        self.assertAlmostEqual(prod_c_stats['sales'], 320.0)
        self.assertAlmostEqual(prod_c_stats['expense'], 200.0)
        self.assertAlmostEqual(prod_c_stats['profit'], 120.0)

        # Test foreign currency conversion branch
        curr_eur = self.env.ref('base.EUR', raise_if_not_found=False)
        curr_usd = self.env.ref('base.USD', raise_if_not_found=False)
        target_curr = (
            curr_eur if self.company.currency_id != curr_eur else curr_usd
        )
        if target_curr:
            target_curr.active = True
            foreign_inv = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': self.partner.id,
                'currency_id': target_curr.id,
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': [
                    fields.Command.create({
                        'product_id': self.product_a.id,
                        'quantity': 1,
                        'price_unit': 50.0,
                    }),
                ],
            })
            foreign_inv.action_post()
            res_fc = report_model._get_report_values([], data)
            self.assertIn(self.product_a.id, res_fc['groups'])

    def test_05_report_single_product_filter_and_validation(self):
        """Test specific product filtering and from_date validation."""
        wizard = self.env['profit.product'].create({
            'company_id': self.company.id,
            'categ_id': self.category_parent.id,
            'from_date': fields.Date.today() - timedelta(days=30),
            'to_date': fields.Date.today() + timedelta(days=1),
        })
        wizard._onchange_categ_id()
        wizard.product_id = self.product_a

        report_model = self.env[
            'report.product_profit_report.product_profit_report'
        ]
        data = {'form': wizard.read([])[0]}
        res = report_model._get_report_values([], data)
        self.assertIn(self.product_a.id, res['groups'])
        self.assertNotIn(self.product_b.id, res['groups'])

        # Validation error when from_date > to_date
        invalid_data = {
            'from_date': fields.Date.today() + timedelta(days=5),
            'to_date': fields.Date.today(),
            'company_id': [self.company.id, self.company.name],
            'product_id': False,
            'product_product_ids': [self.product_a.id],
        }
        with self.assertRaises(ValidationError):
            report_model.generate_report_values(invalid_data)

    def test_06_price_history_automatic_population_on_standard_price_change(self):
        """Test price.history is populated automatically when standard_price changes."""
        test_product = self.env['product.product'].create({
            'name': 'History Auto Tracking Product',
            'categ_id': self.category_child.id,
            'standard_price': 80.0,
        })
        # Update cost via product.product write
        test_product.write({'standard_price': 95.0})
        history_after_write = self.env['price.history'].search([
            ('product_id', '=', test_product.id),
        ], order='datetime desc, id desc')
        self.assertTrue(history_after_write)
        self.assertEqual(history_after_write[0].cost, 95.0)

        # Update cost via product.template standard_price
        test_product.product_tmpl_id.standard_price = 110.0
        history_after_tmpl = self.env['price.history'].search([
            ('product_id', '=', test_product.id),
        ], order='datetime desc, id desc')
        self.assertEqual(history_after_tmpl[0].cost, 110.0)

        # Verify get_history_price retrieves the latest cost
        cost_now = test_product.get_history_price(self.company.id)
        self.assertEqual(cost_now, 110.0)

    def test_07_non_account_user_can_update_standard_price_without_access_error(self):
        """Test non-account user updates standard_price without AccessError (using sudo)."""
        group_user = self.env.ref('base.group_user')
        group_product_manager = self.env.ref('product.group_product_manager')
        product_mgr_user = self.env['res.users'].create({
            'name': 'Product Manager Non-Account',
            'login': 'product_mgr_test',
            'email': 'product_mgr@cybrosys.com',
            'group_ids': [(6, 0, [group_user.id, group_product_manager.id])],
        })
        test_product = self.env['product.product'].create({
            'name': 'Standard Price Access Test Product',
            'categ_id': self.category_child.id,
            'standard_price': 50.0,
        })
        # Product manager (not in account groups) updates standard_price; succeeds via sudo() on price.history
        test_product.with_user(product_mgr_user).write({'standard_price': 65.0})
        self.assertEqual(test_product.standard_price, 65.0)
        history_entry = self.env['price.history'].sudo().search([
            ('product_id', '=', test_product.id),
        ], order='datetime desc, id desc', limit=1)
        self.assertTrue(history_entry)
        self.assertEqual(history_entry.cost, 65.0)
