###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring,protected-access,too-many-statements,too-many-lines
import json
from unittest.mock import MagicMock, patch

from odoo.exceptions import ValidationError
from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install', 'advanced_product_pack')
class TestAdvancedProductPack(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'Pack Test Partner',
        })
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')

        # Create components
        cls.comp_storable = cls.env['product.product'].create({
            'name': 'Component Storable',
            'type': 'consu',
            'list_price': 50.0,
            'standard_price': 30.0,
            'uom_id': cls.uom_unit.id,
        })
        cls.comp_consumable = cls.env['product.product'].create({
            'name': 'Component Consumable',
            'type': 'consu',
            'list_price': 25.0,
            'standard_price': 15.0,
            'uom_id': cls.uom_unit.id,
        })
        cls.comp_service = cls.env['product.product'].create({
            'name': 'Component Service',
            'type': 'service',
            'list_price': 100.0,
            'standard_price': 40.0,
            'uom_id': cls.uom_unit.id,
        })

        # Create Bundle Template
        cls.bundle_template = cls.env['product.template'].create({
            'name': 'Mega Combo Pack',
            'is_bundle': True,
            'calc_pack_price': True,
            'calc_pack_cost': True,
            'bundle_line_ids': [
                Command.create({
                    'product_id': cls.comp_storable.id,
                    'quantity': 2.0,
                }),
                Command.create({
                    'product_id': cls.comp_consumable.id,
                    'quantity': 3.0,
                }),
                Command.create({
                    'product_id': cls.comp_service.id,
                    'quantity': 1.0,
                }),
            ],
        })
        cls.bundle_product = cls.bundle_template.product_variant_id

    def test_01_bundle_prices_and_subtotals(self):
        """Test bundle line subtotals and auto price/cost calculations."""
        # Check bundle line subtotals
        lines = self.bundle_template.bundle_line_ids
        line_storable = lines.filtered(lambda bl: bl.product_id == self.comp_storable)
        line_consu = lines.filtered(lambda bl: bl.product_id == self.comp_consumable)
        line_service = lines.filtered(lambda bl: bl.product_id == self.comp_service)

        self.assertEqual(line_storable.subtotal_price, 100.0)  # 2 * 50
        self.assertEqual(line_storable.subtotal_cost, 60.0)    # 2 * 30
        self.assertEqual(line_consu.subtotal_price, 75.0)     # 3 * 25
        self.assertEqual(line_consu.subtotal_cost, 45.0)      # 3 * 15
        self.assertEqual(line_service.subtotal_price, 100.0)   # 1 * 100
        self.assertEqual(line_service.subtotal_cost, 40.0)     # 1 * 40

        # Trigger onchange in line
        line_storable.quantity = 4.0
        line_storable._onchange_quantity()
        self.assertEqual(line_storable.subtotal_price, 200.0)
        self.assertEqual(line_storable.subtotal_cost, 120.0)

        # Restore quantity and trigger onchange on template
        line_storable.quantity = 2.0
        self.bundle_template._onchange_bundle_pack_prices()

        # Check bundle list_price and standard_price
        expected_price = 100.0 + 75.0 + 100.0
        expected_cost = 60.0 + 45.0 + 40.0
        self.assertEqual(self.bundle_template.list_price, expected_price)
        self.assertEqual(self.bundle_template.standard_price, expected_cost)

        # Check bundle_contents_info JSON
        contents_info = self.bundle_template.bundle_contents_info
        self.assertTrue(contents_info)
        details = json.loads(contents_info)
        self.assertEqual(len(details), 3)

        # Non-bundle template has no bundle_contents_info
        non_bundle = self.env['product.template'].create({
            'name': 'Regular Product',
            'is_bundle': False,
        })
        self.assertFalse(non_bundle.bundle_contents_info)

    def test_02_bundle_price_sync_on_component_updates(self):
        """Test that updating component prices automatically triggers bundle updates."""
        # 1. Update component list price through template
        self.comp_storable.product_tmpl_id.write({
            'list_price': 60.0,
            'standard_price': 35.0,
        })
        # Expected new price: (2 * 60) + 75 + 100 = 295.0
        # Expected new cost: (2 * 35) + 45 + 40 = 155.0
        self.assertEqual(self.bundle_template.list_price, 295.0)
        self.assertEqual(self.bundle_template.standard_price, 155.0)

        # 2. Update component variant price directly
        self.comp_consumable.write({
            'lst_price': 30.0,
            'standard_price': 20.0,
        })
        # Expected new price: 120 + (3 * 30) + 100 = 310.0
        # Expected new cost: 70 + (3 * 20) + 40 = 170.0
        self.assertEqual(self.bundle_template.list_price, 310.0)
        self.assertEqual(self.bundle_template.standard_price, 170.0)

    def test_03_variant_constraint(self):
        """Test that bundles cannot have variants."""
        attribute = self.env['product.attribute'].create({
            'name': 'Size',
            'value_ids': [
                Command.create({'name': 'Small'}),
                Command.create({'name': 'Large'}),
            ],
        })
        with self.assertRaises(ValidationError):
            self.bundle_template.write({
                'attribute_line_ids': [
                    Command.create({
                        'attribute_id': attribute.id,
                        'value_ids': [Command.set(attribute.value_ids.ids)],
                    }),
                ],
            })

    def test_04_ribbon_and_pos_fields(self):
        """Test bundle ribbon and PoS field inclusions."""
        # Test ribbon
        ribbon = self.bundle_template._get_ribbon()
        self.assertTrue(ribbon)
        self.assertEqual(ribbon.name, 'Pack')

        non_bundle = self.env['product.template'].create({
            'name': 'Standard Non-Bundle',
            'is_bundle': False,
        })
        self.assertFalse(non_bundle._get_ribbon())

        # Test PoS data fields
        pos_config = self.env['pos.config'].create({
            'name': 'Test Ribbon Config',
        })
        pos_tmpl_fields = self.env['product.template']._load_pos_data_fields(pos_config)
        self.assertIn('is_bundle', pos_tmpl_fields)
        self.assertIn('bundle_contents_info', pos_tmpl_fields)

        pos_prod_fields = self.env['product.product']._load_pos_data_fields(pos_config)
        self.assertIn('is_bundle', pos_prod_fields)
        self.assertIn('bundle_contents_info', pos_prod_fields)

    def test_05_sale_order_explosion(self):
        """Test sale order confirmation and component explosion."""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.bundle_product.id,
                    'product_uom_qty': 2.0,
                    'price_unit': self.bundle_product.lst_price,
                }),
            ],
        })

        # Test skip_procurement context
        res = sale_order.order_line.with_context(
            skip_procurement=True,
        )._action_launch_stock_rule()
        self.assertTrue(res)

        # Confirm sale order
        sale_order.action_confirm()

        # Check picking moves for storable/consumable components
        self.assertTrue(sale_order.picking_ids)
        picking = sale_order.picking_ids[0]
        move_products = picking.move_ids.mapped('product_id')
        self.assertIn(self.comp_storable, move_products)
        self.assertIn(self.comp_consumable, move_products)

        # Check shadow sale order line for service component
        service_sol = sale_order.order_line.filtered(
            lambda sol: sol.product_id == self.comp_service,
        )
        self.assertTrue(service_sol)
        self.assertTrue(service_sol.is_pack_component)
        self.assertEqual(service_sol.price_unit, 0.0)

    def test_06_pos_order_line_and_receipt(self):
        """Test PoS receipt generation and bundle contents parsing."""
        # Create a PoS session
        pos_config = self.env['pos.config'].create({
            'name': 'Bundle Test Shop',
        })
        pos_session = self.env['pos.session'].create({
            'config_id': pos_config.id,
        })

        pos_order = self.env['pos.order'].create({
            'company_id': self.company.id,
            'session_id': pos_session.id,
            'partner_id': self.partner.id,
            'lines': [
                Command.create({
                    'product_id': self.bundle_product.id,
                    'qty': 1.0,
                    'price_unit': self.bundle_product.lst_price,
                    'price_subtotal': self.bundle_product.lst_price,
                    'price_subtotal_incl': self.bundle_product.lst_price,
                }),
                Command.create({
                    'product_id': self.comp_storable.id,
                    'qty': 1.0,
                    'price_unit': self.comp_storable.lst_price,
                    'price_subtotal': self.comp_storable.lst_price,
                    'price_subtotal_incl': self.comp_storable.lst_price,
                }),
            ],
            'amount_tax': 0.0,
            'amount_total': self.bundle_product.lst_price + self.comp_storable.lst_price,
            'amount_paid': self.bundle_product.lst_price + self.comp_storable.lst_price,
            'amount_return': 0.0,
        })

        # Test receipt generation
        receipt_data = pos_order._order_receipt_generate_line_data()
        self.assertEqual(len(receipt_data), 2)
        bundle_receipt_line = receipt_data[0]
        self.assertTrue(bundle_receipt_line.get('bundle_details'))
        self.assertEqual(len(bundle_receipt_line['bundle_details']), 3)

        # Test receipt with corrupted JSON to trigger error handling
        bad_product = self.env['product.product'].create({
            'name': 'Corrupted Bundle Product',
            'is_bundle': True,
        })
        bad_product.bundle_contents_info = "{corrupted json"
        pos_order_bad = self.env['pos.order'].create({
            'company_id': self.company.id,
            'session_id': pos_session.id,
            'partner_id': self.partner.id,
            'lines': [
                Command.create({
                    'product_id': bad_product.id,
                    'qty': 1.0,
                    'price_unit': 10.0,
                    'price_subtotal': 10.0,
                    'price_subtotal_incl': 10.0,
                }),
            ],
            'amount_tax': 0.0,
            'amount_total': 10.0,
            'amount_paid': 10.0,
            'amount_return': 0.0,
        })
        bad_receipt = pos_order_bad._order_receipt_generate_line_data()
        self.assertFalse(bad_receipt[0].get('bundle_details'))

        # Test _launch_stock_rule_from_pos_order_lines with mocked procurement run
        with patch('odoo.addons.stock.models.stock_rule.StockRule.run', MagicMock()):
            pos_order.lines._launch_stock_rule_from_pos_order_lines()

    def test_07_stock_picking_pos_explosion(self):
        """Test stock.picking._create_move_from_pos_order_lines."""
        pos_config = self.env['pos.config'].create({
            'name': 'Stock Picking Test Shop',
        })
        pos_session = self.env['pos.session'].create({
            'config_id': pos_config.id,
        })
        pos_order = self.env['pos.order'].create({
            'company_id': self.company.id,
            'session_id': pos_session.id,
            'partner_id': self.partner.id,
            'lines': [
                Command.create({
                    'product_id': self.bundle_product.id,
                    'qty': 1.0,
                    'price_unit': self.bundle_product.lst_price,
                    'price_subtotal': self.bundle_product.lst_price,
                    'price_subtotal_incl': self.bundle_product.lst_price,
                }),
                Command.create({
                    'product_id': self.comp_storable.id,
                    'qty': 2.0,
                    'price_unit': self.comp_storable.lst_price,
                    'price_subtotal': 2 * self.comp_storable.lst_price,
                    'price_subtotal_incl': 2 * self.comp_storable.lst_price,
                }),
            ],
            'amount_tax': 0.0,
            'amount_total': self.bundle_product.lst_price + 2 * self.comp_storable.lst_price,
            'amount_paid': self.bundle_product.lst_price + 2 * self.comp_storable.lst_price,
            'amount_return': 0.0,
        })

        warehouse = self.env['stock.warehouse'].search([
            ('company_id', '=', self.company.id),
        ], limit=1)
        picking = self.env['stock.picking'].create({
            'picking_type_id': warehouse.out_type_id.id,
            'location_id': warehouse.lot_stock_id.id,
            'location_dest_id': self.partner.property_stock_customer.id,
            'company_id': self.company.id,
        })

        picking._create_move_from_pos_order_lines(pos_order.lines)
        self.assertTrue(picking.move_ids)
        # Component storable (from bundle) + Component consumable (from bundle) + Regular storable
        moved_products = picking.move_ids.mapped('product_id')
        self.assertIn(self.comp_storable, moved_products)
        self.assertIn(self.comp_consumable, moved_products)

    def test_08_project_task_state(self):
        """Test custom 00_new state handling in project.task."""
        project = self.env['project.project'].create({
            'name': 'Bundle Test Project',
        })
        task = self.env['project.task'].create({
            'name': 'Bundle Service Task',
            'project_id': project.id,
            'state': '00_new',
        })
        self.assertEqual(task.state, '00_new')
        task._compute_state()
        self.assertEqual(task.state, '00_new')
