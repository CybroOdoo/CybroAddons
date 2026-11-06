# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo.tests import TransactionCase, tagged

PARAM_KEY = 'pos_load_products_location.source_loc_id'


@tagged('post_install', '-at_install')
class TestPosLoadProductsLocation(TransactionCase):
    """Tests for the location based product filter of the POS."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        location_model = cls.env['stock.location']
        cls.parent_location = location_model.create({
            'name': 'Test Parent Location',
            'usage': 'internal',
        })
        cls.child_location = location_model.create({
            'name': 'Test Child Location',
            'usage': 'internal',
            'location_id': cls.parent_location.id,
        })
        cls.other_location = location_model.create({
            'name': 'Test Other Location',
            'usage': 'internal',
        })
        product_model = cls.env['product.product']
        cls.product_parent = product_model.create({
            'name': 'Test Product Parent',
            'is_storable': True,
        })
        cls.product_child = product_model.create({
            'name': 'Test Product Child',
            'is_storable': True,
        })
        cls.product_other = product_model.create({
            'name': 'Test Product Other',
            'is_storable': True,
        })
        cls.product_no_stock = product_model.create({
            'name': 'Test Product No Stock',
            'is_storable': True,
        })
        quant_model = cls.env['stock.quant']
        quant_model._update_available_quantity(
            cls.product_parent, cls.parent_location, 5)
        quant_model._update_available_quantity(
            cls.product_child, cls.child_location, 3)
        quant_model._update_available_quantity(
            cls.product_other, cls.other_location, 7)

    def _set_location(self, location_id):
        """Store or clear the selected stock location in the parameters."""
        param_model = self.env['ir.config_parameter'].sudo()
        param = param_model.search([('key', '=', PARAM_KEY)])
        if not location_id:
            param.unlink()
        elif param:
            param.write({'value': str(location_id)})
        else:
            param_model.create({'key': PARAM_KEY, 'value': str(location_id)})

    def test_no_location_selected(self):
        """Without a selected location, no restriction is applied."""
        self._set_location(False)
        result = self.env['stock.location'].search_products_by_location()
        self.assertFalse(result)

    def test_deleted_location_selected(self):
        """A location id that does not exist applies no restriction."""
        self._set_location(self.env['stock.location'].search(
            [], order='id desc', limit=1).id + 1000)
        result = self.env['stock.location'].search_products_by_location()
        self.assertFalse(result)

    def test_products_in_selected_location(self):
        """Only products with stock in the location are returned."""
        self._set_location(self.child_location.id)
        result = self.env['stock.location'].search_products_by_location()
        self.assertIn(self.product_child.product_tmpl_id.id, result)
        self.assertNotIn(self.product_parent.product_tmpl_id.id, result)
        self.assertNotIn(self.product_other.product_tmpl_id.id, result)
        self.assertNotIn(self.product_no_stock.product_tmpl_id.id, result)

    def test_child_locations_are_included(self):
        """Products stocked in sub-locations are returned for the parent."""
        self._set_location(self.parent_location.id)
        result = self.env['stock.location'].search_products_by_location()
        self.assertIn(self.product_parent.product_tmpl_id.id, result)
        self.assertIn(self.product_child.product_tmpl_id.id, result)
        self.assertNotIn(self.product_other.product_tmpl_id.id, result)

    def test_location_without_stock_returns_empty_list(self):
        """An empty location returns an empty list, not False."""
        empty_location = self.env['stock.location'].create({
            'name': 'Test Empty Location',
            'usage': 'internal',
        })
        self._set_location(empty_location.id)
        result = self.env['stock.location'].search_products_by_location()
        self.assertEqual(result, [])

    def test_zero_quantity_products_are_excluded(self):
        """Products whose stock dropped to zero are not returned."""
        self.env['stock.quant']._update_available_quantity(
            self.product_other, self.other_location, -7)
        self._set_location(self.other_location.id)
        result = self.env['stock.location'].search_products_by_location()
        self.assertNotIn(self.product_other.product_tmpl_id.id, result)

    def test_settings_store_location(self):
        """The settings field saves the location in the system parameters."""
        settings = self.env['res.config.settings'].create({
            'source_loc_id': self.child_location.id,
        })
        settings.set_values()
        stored = self.env['ir.config_parameter'].sudo().get_int(PARAM_KEY)
        self.assertEqual(stored, self.child_location.id)
