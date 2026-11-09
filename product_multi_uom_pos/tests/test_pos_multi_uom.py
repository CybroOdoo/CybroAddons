# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Arshad Ali Pottengal (Contact : odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from unittest.mock import patch
from psycopg2 import IntegrityError

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import common, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestProductMultiUomPos(common.TransactionCase):
    """Test suite for POS Product Multiple UOM module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_unit = cls.env.ref(
            'uom.product_uom_unit', raise_if_not_found=False
        )
        if not cls.uom_unit:
            cls.uom_unit = cls.env['uom.uom'].create({
                'name': 'Unit',
                'relative_factor': 1.0,
            })
        cls.uom_box = cls.env['uom.uom'].search([
            ('relative_uom_id', '=', cls.uom_unit.id),
            ('id', '!=', cls.uom_unit.id),
        ], limit=1)
        if not cls.uom_box:
            cls.uom_box = cls.env['uom.uom'].create({
                'name': 'Box of 10',
                'relative_uom_id': cls.uom_unit.id,
                'relative_factor': 10.0,
            })

        cls.product = cls.env['product.product'].create({
            'name': 'Test Bagel',
            'type': 'consu',
            'uom_id': cls.uom_unit.id,
            'list_price': 10.0,
        })
        cls.product_template = cls.product.product_tmpl_id

        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test POS Shop',
        })
        cls.pos_session = cls.env['pos.session'].create({
            'config_id': cls.pos_config.id,
        })

    def test_pos_multi_uom_crud(self):
        """Test creating, reading, updating and deleting pos.multi.uom."""
        multi_uom = self.env['pos.multi.uom'].create({
            'product_template_id': self.product_template.id,
            'uom_id': self.uom_box.id,
            'factor': 10.0,
            'price': 90.0,
        })
        self.assertEqual(multi_uom.product_template_id, self.product_template)
        self.assertEqual(multi_uom.uom_id, self.uom_box)
        self.assertEqual(multi_uom.factor, 10.0)
        self.assertEqual(multi_uom.price, 90.0)
        self.assertIn(multi_uom, self.product_template.pos_multi_uom_ids)
        self.assertEqual(multi_uom.display_name, self.uom_box.display_name)

        multi_uom.write({'price': 95.0, 'factor': 12.0})
        self.assertEqual(multi_uom.price, 95.0)
        self.assertEqual(multi_uom.factor, 12.0)

        multi_uom_id = multi_uom.id
        multi_uom.unlink()
        self.assertFalse(
            self.env['pos.multi.uom'].browse(multi_uom_id).exists()
        )

        default_multi = self.env['pos.multi.uom'].create({
            'product_template_id': self.product_template.id,
            'uom_id': self.uom_unit.id,
        })
        self.assertEqual(default_multi.factor, 1.0)
        self.assertEqual(default_multi.price, 0.0)

    def test_pos_multi_uom_cascade_delete(self):
        """Deleting product template cascade-deletes related pos.multi.uom."""
        temp_product = self.env['product.product'].create({
            'name': 'Cascade Delete Product',
            'type': 'consu',
            'uom_id': self.uom_unit.id,
            'list_price': 5.0,
        })
        temp_multi = self.env['pos.multi.uom'].create({
            'product_template_id': temp_product.product_tmpl_id.id,
            'uom_id': self.uom_box.id,
            'factor': 5.0,
            'price': 25.0,
        })
        temp_multi_id = temp_multi.id
        temp_product.product_tmpl_id.unlink()
        self.assertFalse(
            self.env['pos.multi.uom'].browse(temp_multi_id).exists()
        )

    def test_pos_multi_uom_factor_constraint(self):
        """Factor must be strictly greater than zero."""
        with self.assertRaises(ValidationError):
            self.env['pos.multi.uom'].create({
                'product_template_id': self.product_template.id,
                'uom_id': self.uom_box.id,
                'factor': 0.0,
                'price': 10.0,
            })

        with self.assertRaises(ValidationError):
            self.env['pos.multi.uom'].create({
                'product_template_id': self.product_template.id,
                'uom_id': self.uom_box.id,
                'factor': -2.5,
                'price': 10.0,
            })

    def test_pos_multi_uom_unique_constraint(self):
        """Cannot define same UoM more than once for a single product."""
        self.env['pos.multi.uom'].create({
            'product_template_id': self.product_template.id,
            'uom_id': self.uom_box.id,
            'factor': 10.0,
            'price': 90.0,
        })
        with mute_logger('odoo.sql_db'), self.assertRaises(
            (IntegrityError, ValidationError)
        ):
            with self.cr.savepoint():
                self.env['pos.multi.uom'].create({
                    'product_template_id': self.product_template.id,
                    'uom_id': self.uom_box.id,
                    'factor': 5.0,
                    'price': 50.0,
                })

    def test_pos_data_loading_hooks(self):
        """Verify pos.multi.uom and pos.session POS data loading methods."""
        multi_uom_fields = self.env['pos.multi.uom']._load_pos_data_fields(
            self.pos_config
        )
        self.assertIn('uom_id', multi_uom_fields)
        self.assertIn('product_template_id', multi_uom_fields)
        self.assertIn('factor', multi_uom_fields)
        self.assertIn('price', multi_uom_fields)

        domain = self.env['pos.multi.uom']._load_pos_data_domain({})
        self.assertIsInstance(domain, list)

        loaded_models = self.env['pos.session']._load_pos_data_models(
            self.pos_config
        )
        self.assertIn('pos.multi.uom', loaded_models)

    def test_product_template_multi_uom_computation(self):
        """multi_uom reflects system parameter status."""
        param_model = self.env['ir.config_parameter'].sudo()

        param_model.set_bool('product_multi_uom_pos.pos_multi_uom', True)
        self.product_template._compute_multi_uom()
        self.assertTrue(self.product_template.multi_uom)

        param_model.set_bool('product_multi_uom_pos.pos_multi_uom', False)
        self.product_template._compute_multi_uom()
        self.assertFalse(self.product_template.multi_uom)

    def test_product_product_load_pos_data_fields(self):
        """_load_pos_data_fields includes product_tmpl_id."""
        product_fields = self.env['product.product']._load_pos_data_fields(
            self.pos_config
        )
        self.assertIn('product_tmpl_id', product_fields)

        # Test integer ID fallback
        product_fields_int = (
            self.env['product.product']._load_pos_data_fields(
                self.pos_config.id
            )
        )
        self.assertIn('product_tmpl_id', product_fields_int)

        # Test deduplication when already in fields list
        with patch.object(
            type(self.env['product.product']),
            '_load_pos_data_fields',
            autospec=True,
            return_value=['id', 'name', 'product_tmpl_id']
        ):
            already_present = (
                self.env['product.product']._load_pos_data_fields(
                    self.pos_config
                )
            )
            self.assertEqual(already_present.count('product_tmpl_id'), 1)

    def test_pos_config_fields_and_read(self):
        """Test pos.config pos_multi_uom field and read method override."""
        self.pos_config.write({'pos_multi_uom': True})
        self.assertTrue(self.pos_config.pos_multi_uom)

        res = self.pos_config.read(['name', 'pos_multi_uom'])
        self.assertTrue(res)
        self.assertTrue(res[0].get('pos_multi_uom'))

        self.pos_config.write({'pos_multi_uom': False})
        self.assertFalse(self.pos_config.pos_multi_uom)

        res_all = self.pos_config.read()
        self.assertTrue(res_all)

    def test_res_config_settings_multi_uom(self):
        """Verify pos_multi_uom in res.config.settings writes to params."""
        param = 'product_multi_uom_pos.pos_multi_uom'
        settings_enabled = self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
            'pos_multi_uom': True,
        })
        settings_enabled.execute()
        is_enabled = self.env['ir.config_parameter'].sudo().get_bool(param)
        self.assertTrue(is_enabled)
        self.assertTrue(self.pos_config.pos_multi_uom)

        settings_disabled = self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
            'pos_multi_uom': False,
        })
        settings_disabled.execute()
        is_disabled = self.env['ir.config_parameter'].sudo().get_bool(param)
        self.assertFalse(is_disabled)
        self.assertFalse(self.pos_config.pos_multi_uom)

    def test_pos_order_line_compute_product_uom_id(self):
        """_compute_product_uom_id defaults to product.uom_id when empty."""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'lines': [
                Command.create({
                    'product_id': self.product.id,
                    'qty': 1.0,
                    'price_unit': 10.0,
                    'price_subtotal': 10.0,
                    'price_subtotal_incl': 10.0,
                }),
                Command.create({
                    'product_id': self.product.id,
                    'qty': 1.0,
                    'price_unit': 90.0,
                    'price_subtotal': 90.0,
                    'price_subtotal_incl': 90.0,
                    'product_uom_id': self.uom_box.id,
                    'custom_uom_name': 'Box of 10',
                    'custom_uom_price': 90.0,
                }),
            ],
            'amount_total': 100.0,
            'amount_tax': 0.0,
            'amount_paid': 100.0,
            'amount_return': 0.0,
        })
        line_default_uom = order.lines[0]
        line_custom_uom = order.lines[1]

        self.assertEqual(line_default_uom.product_uom_id, self.product.uom_id)
        self.assertEqual(line_custom_uom.product_uom_id, self.uom_box)

    def test_pos_order_line_load_pos_data_fields(self):
        """_load_pos_data_fields includes custom UoM fields."""
        fields_list = self.env['pos.order.line']._load_pos_data_fields(
            self.pos_config
        )
        self.assertIn('custom_uom_name', fields_list)
        self.assertIn('custom_uom_price', fields_list)
        self.assertIn('product_uom_id', fields_list)

    def test_pos_order_receipt_generate_line_data(self):
        """_order_receipt_generate_line_data covers all branches."""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'lines': [
                Command.create({
                    'product_id': self.product.id,
                    'qty': 1.0,
                    'price_unit': 45.0,
                    'price_subtotal': 45.0,
                    'price_subtotal_incl': 45.0,
                    'product_uom_id': self.uom_box.id,
                    'custom_uom_name': 'Box of 10',
                    'custom_uom_price': 45.0,
                }),
                Command.create({
                    'product_id': self.product.id,
                    'qty': 1.0,
                    'price_unit': 10.0,
                    'price_subtotal': 10.0,
                    'price_subtotal_incl': 10.0,
                    'product_uom_id': self.uom_unit.id,
                }),
                Command.create({
                    'product_id': self.product.id,
                    'qty': 1.0,
                    'price_unit': 10.0,
                    'price_subtotal': 10.0,
                    'price_subtotal_incl': 10.0,
                }),
            ],
            'amount_total': 65.0,
            'amount_tax': 0.0,
            'amount_paid': 65.0,
            'amount_return': 0.0,
        })
        order.lines[2].product_uom_id = False

        lines_data = order._order_receipt_generate_line_data()
        self.assertEqual(len(lines_data), 3)
        # Line 1: custom_uom_name takes precedence
        self.assertEqual(lines_data[0].get('product_uom_name'), 'Box of 10')
        # Line 2: fallback to product_uom_id.name
        self.assertEqual(
            lines_data[1].get('product_uom_name'), self.uom_unit.name
        )
        # Line 3: neither set, retains super() value
        self.assertFalse(lines_data[2].get('custom_uom_name'))

    def test_stock_picking_prepare_stock_move_vals(self):
        """_prepare_stock_move_vals uses line.product_uom_id when present."""
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'lines': [
                Command.create({
                    'product_id': self.product.id,
                    'qty': 1.0,
                    'price_unit': 45.0,
                    'price_subtotal': 45.0,
                    'price_subtotal_incl': 45.0,
                    'product_uom_id': self.uom_box.id,
                    'custom_uom_name': 'Box of 10',
                    'custom_uom_price': 45.0,
                }),
                Command.create({
                    'product_id': self.product.id,
                    'qty': 1.0,
                    'price_unit': 10.0,
                    'price_subtotal': 10.0,
                    'price_subtotal_incl': 10.0,
                }),
            ],
            'amount_total': 55.0,
            'amount_tax': 0.0,
            'amount_paid': 55.0,
            'amount_return': 0.0,
        })
        line_with_uom = order.lines[0]
        line_without_uom = order.lines[1]
        line_without_uom.product_uom_id = False

        stock_type_model = self.env['stock.picking.type']
        company_id = self.env.company.id
        picking_type = (
            getattr(self.pos_config, 'picking_type_id', False)
            or stock_type_model.search(
                [('warehouse_id.company_id', '=', company_id)], limit=1
            )
            or stock_type_model.search([], limit=1)
        )
        if not picking_type:
            picking_type = stock_type_model.create({
                'name': 'POS Outgoing Test',
                'code': 'outgoing',
                'sequence_code': 'POS_OUT',
            })

        loc_stock = self.env.ref(
            'stock.stock_location_stock', raise_if_not_found=False
        )
        loc_customers = self.env.ref(
            'stock.stock_location_customers', raise_if_not_found=False
        )
        location_src = (
            picking_type.default_location_src_id or loc_stock
        )
        location_dest = (
            picking_type.default_location_dest_id or loc_customers
        )
        if not location_src or not location_dest:
            location_src = self.env['stock.location'].create({
                'name': 'Test Stock Src',
                'usage': 'internal',
            })
            location_dest = self.env['stock.location'].create({
                'name': 'Test Stock Dest',
                'usage': 'customer',
            })

        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': location_src.id,
            'location_dest_id': location_dest.id,
        })

        move_vals_with_uom = picking._prepare_stock_move_vals(
            line_with_uom, line_with_uom
        )
        self.assertEqual(move_vals_with_uom['uom_id'], self.uom_box.id)

        move_vals_no_uom = picking._prepare_stock_move_vals(
            line_without_uom, line_without_uom
        )
        self.assertEqual(move_vals_no_uom['uom_id'], self.product.uom_id.id)
