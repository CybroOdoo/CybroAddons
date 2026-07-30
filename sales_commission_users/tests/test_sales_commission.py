# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anjali V P (<https://www.cybrosys.com>)
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
from datetime import date
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from odoo.fields import Command


class TestSalesCommission(TransactionCase):
    """Test cases for sales commission module."""

    @classmethod
    def setUpClass(cls):
        super(TestSalesCommission, cls).setUpClass()

        # Create a salesperson user
        cls.salesperson = cls.env['res.users'].create({
            'name': 'Salesperson Test',
            'login': 'salesperson_test',
            'email': 'salesperson_test@example.com',
            'groups_id': [Command.link(cls.env.ref('base.group_user').id)],
        })

        # Create another salesperson user for testing UserError in action_create_invoice
        cls.salesperson_other = cls.env['res.users'].create({
            'name': 'Salesperson Other',
            'login': 'salesperson_other',
            'email': 'salesperson_other@example.com',
            'groups_id': [Command.link(cls.env.ref('base.group_user').id)],
        })

        # Create customers
        cls.partner_affiliated = cls.env['res.partner'].create({
            'name': 'Affiliated Customer',
            'affiliated': True,
        })
        cls.partner_non_affiliated = cls.env['res.partner'].create({
            'name': 'Non-Affiliated Customer',
            'affiliated': False,
        })

        # Create products
        cls.product_a = cls.env['product.product'].create({
            'name': 'Product A',
            'list_price': 100.0,
            'lst_price': 100.0,
        })
        cls.product_b = cls.env['product.product'].create({
            'name': 'Product B',
            'list_price': 200.0,
            'lst_price': 200.0,
        })

    def test_01_standard_commission(self):
        """Test standard sales commission calculation on SO confirmation."""
        # Create standard commission config
        commission_config = self.env['sales.commission'].create({
            'name': 'Standard Commission 10%',
            'commission_type': 'standard',
            'sales_person_ids': [Command.link(self.salesperson.id)],
            'std_commission_perc': 10.0,
        })

        # Create Sale Order
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_non_affiliated.id,
            'user_id': self.salesperson.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 2.0,
                    'price_unit': 100.0,
                    'tax_id': [Command.clear()],
                })
            ]
        })
        # Confirm Sale Order
        sale_order.action_confirm()

        # Check commission lines
        self.assertEqual(len(sale_order.commission_ids), 1, "There should be one commission line created.")
        commission_line = sale_order.commission_ids[0]
        self.assertEqual(commission_line.commission_type, 'standard')
        self.assertEqual(commission_line.sales_person_id, self.salesperson)
        # Expected commission: 200.0 * 10 / 100 = 20.0
        self.assertAlmostEqual(commission_line.commission_amount, 20.0)
        self.assertEqual(commission_line.partner_id, self.partner_non_affiliated)
        self.assertEqual(commission_line.commission, 'Standard Commission 10%')

    def test_02_partner_based_commission(self):
        """Test partner-based sales commission calculation on SO confirmation."""
        # Create partner-based commission config
        commission_config = self.env['sales.commission'].create({
            'name': 'Partner Based Commission',
            'commission_type': 'partner_based',
            'sales_person_ids': [Command.link(self.salesperson.id)],
            'affiliated_commission_perc': 15.0,
            'non_affiliated_commission_perc': 5.0,
        })

        # Test Case A: Affiliated Partner
        so_affiliated = self.env['sale.order'].create({
            'partner_id': self.partner_affiliated.id,
            'user_id': self.salesperson.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 1.0,
                    'price_unit': 100.0,
                    'tax_id': [Command.clear()],
                })
            ]
        })
        so_affiliated.action_confirm()
        self.assertEqual(len(so_affiliated.commission_ids), 1)
        # Expected: 100.0 * 15 / 100 = 15.0
        self.assertAlmostEqual(so_affiliated.commission_ids[0].commission_amount, 15.0)

        # Test Case B: Non-Affiliated Partner
        so_non_affiliated = self.env['sale.order'].create({
            'partner_id': self.partner_non_affiliated.id,
            'user_id': self.salesperson.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 1.0,
                    'price_unit': 100.0,
                    'tax_id': [Command.clear()],
                })
            ]
        })
        so_non_affiliated.action_confirm()
        self.assertEqual(len(so_non_affiliated.commission_ids), 1)
        # Expected: 100.0 * 5 / 100 = 5.0
        self.assertAlmostEqual(so_non_affiliated.commission_ids[0].commission_amount, 5.0)

    def test_03_product_based_commission(self):
        """Test product-based sales commission calculation on SO confirmation."""
        # Create product-based commission config
        commission_config = self.env['sales.commission'].create({
            'name': 'Product Based Commission',
            'commission_type': 'product_based',
            'sales_person_ids': [Command.link(self.salesperson.id)],
            'product_based_ids': [
                Command.create({
                    'product_id': self.product_a.id,
                    'commission': 12.0,
                }),
                Command.create({
                    'product_id': self.product_b.id,
                    'commission': 8.0,
                })
            ]
        })

        # Create Sale Order with both products
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_non_affiliated.id,
            'user_id': self.salesperson.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 1.0,
                    'price_unit': 100.0,
                    'tax_id': [Command.clear()],
                }),
                Command.create({
                    'product_id': self.product_b.id,
                    'product_uom_qty': 1.0,
                    'price_unit': 200.0,
                    'tax_id': [Command.clear()],
                })
            ]
        })
        sale_order.action_confirm()

        # Product A: list_price is 100.0. commission is 12.0. Expected = 12.0.
        # Product B: list_price is 200.0. commission is 8.0. Expected = 16.0.
        # Total expected commission_amount = 12.0 + 16.0 = 28.0.
        self.assertEqual(len(sale_order.commission_ids), 1)
        self.assertAlmostEqual(sale_order.commission_ids[0].commission_amount, 28.0)

    def test_04_discount_based_commission(self):
        """Test discount-based sales commission calculation on SO confirmation."""
        # Create discount-based commission config
        commission_config = self.env['sales.commission'].create({
            'name': 'Discount Based Commission',
            'commission_type': 'discount_based',
            'sales_person_ids': [Command.link(self.salesperson.id)],
            'discount_based_ids': [
                Command.create({
                    'discount': 10.0,
                    'commission': 5.0,
                })
            ]
        })

        # Create Sale Order with a discount >= 10.0
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_non_affiliated.id,
            'user_id': self.salesperson.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 1.0,
                    'price_unit': 100.0,
                    'discount': 15.0,
                    'tax_id': [Command.clear()],
                })
            ]
        })
        sale_order.action_confirm()

        # Expected commission: total (85.0) * 5 / 100 = 4.25
        self.assertEqual(len(sale_order.commission_ids), 1)
        self.assertAlmostEqual(sale_order.commission_ids[0].commission_amount, 4.25)

    def test_05_action_create_invoice(self):
        """Test creating invoice from commission lines."""
        # Create standard commission config and lines
        self.env['sales.commission'].create({
            'name': 'Standard Commission',
            'commission_type': 'standard',
            'sales_person_ids': [Command.link(self.salesperson.id)],
            'std_commission_perc': 10.0,
        })
        sale_order_1 = self.env['sale.order'].create({
            'partner_id': self.partner_non_affiliated.id,
            'user_id': self.salesperson.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 1.0,
                    'price_unit': 100.0,
                    'tax_id': [Command.clear()],
                })
            ]
        })
        sale_order_1.action_confirm()

        sale_order_2 = self.env['sale.order'].create({
            'partner_id': self.partner_non_affiliated.id,
            'user_id': self.salesperson.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 1.0,
                    'price_unit': 200.0,
                    'tax_id': [Command.clear()],
                })
            ]
        })
        sale_order_2.action_confirm()

        commission_lines = sale_order_1.commission_ids + sale_order_2.commission_ids
        self.assertEqual(len(commission_lines), 2)

        # Call action_create_invoice
        action = commission_lines.action_create_invoice()
        self.assertTrue(action)
        invoice_id = action.get('res_id')
        self.assertTrue(invoice_id)

        invoice = self.env['account.move'].browse(invoice_id)
        self.assertEqual(invoice.move_type, 'out_invoice')
        self.assertEqual(invoice.partner_id, self.salesperson.partner_id)
        self.assertEqual(len(invoice.invoice_line_ids), 2)

        # Check line details
        self.assertEqual(invoice.invoice_line_ids[0].price_unit, commission_lines[0].commission_amount)
        self.assertEqual(invoice.invoice_line_ids[1].price_unit, commission_lines[1].commission_amount)

        # Test error when multiple salespeople are selected
        self.env['sales.commission'].create({
            'name': 'Other Standard Commission',
            'commission_type': 'standard',
            'sales_person_ids': [Command.link(self.salesperson_other.id)],
            'std_commission_perc': 10.0,
        })
        sale_order_other = self.env['sale.order'].create({
            'partner_id': self.partner_non_affiliated.id,
            'user_id': self.salesperson_other.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 1.0,
                    'price_unit': 100.0,
                    'tax_id': [Command.clear()],
                })
            ]
        })
        sale_order_other.action_confirm()

        all_commission_lines = commission_lines + sale_order_other.commission_ids
        with self.assertRaises(UserError):
            all_commission_lines.action_create_invoice()

    def test_06_reports_and_wizards(self):
        """Test wizard and PDF report generation values."""
        # Create some commission lines for salesperson
        self.env['sales.commission'].create({
            'name': 'Standard Commission',
            'commission_type': 'standard',
            'sales_person_ids': [Command.link(self.salesperson.id)],
            'std_commission_perc': 10.0,
        })
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_non_affiliated.id,
            'user_id': self.salesperson.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 1.0,
                    'price_unit': 100.0,
                    'tax_id': [Command.clear()],
                })
            ]
        })
        sale_order.action_confirm()

        # Instantiate wizard
        wizard = self.env['sales.commission.report'].create({
            'sales_person_id': self.salesperson.id,
            'start_date': date(2026, 1, 1),
            'end_date': date(2026, 12, 31),
        })

        # Trigger wizard action print
        report_action = wizard.action_print_report()
        self.assertEqual(report_action.get('report_name'), 'sales_commission_users.report_sales_commission')

        # Test AbstractReport _get_report_values directly
        report_model = self.env['report.sales_commission_users.report_sales_commission']

        # Call with empty docids and data (coming from wizard)
        wizard_data = {
            'sales_person_id': self.salesperson.name,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
        }
        res = report_model._get_report_values(docids=None, data=wizard_data)
        self.assertTrue(res)
        self.assertIn('docs', res)
        # Verify that the query found exactly 1 commission line due to our bugfix in report
        self.assertEqual(len(res['docs']), 1, "The report should fetch the commission line for the salesperson.")
