# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Prathyunnan R(<https://www.cybrosys.com>)
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


@tagged('post_install', '-at_install')
class TestProductTemplate(TransactionCase):
    """Test cases for product.template functions defined in
    pos_alternative_products/models/product_template.py"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test POS Config Product Template',
        })

    # -----------------------------------------------------------------
    # Tests for _load_pos_data_fields
    # -----------------------------------------------------------------

    def test_load_pos_data_fields_includes_qty_available(self):
        """_load_pos_data_fields must include 'qty_available' so that stock
        quantity information is exposed to the POS frontend."""
        result = self.env['product.template']._load_pos_data_fields(
            self.pos_config.id)
        self.assertIn(
            'qty_available', result,
            "'qty_available' must be in the POS data fields for product.template."
        )

    def test_load_pos_data_fields_includes_alternative_product_ids(self):
        """_load_pos_data_fields must include 'alternative_product_ids' so that
        alternative products can be resolved in the POS frontend."""
        result = self.env['product.template']._load_pos_data_fields(
            self.pos_config.id)
        self.assertIn(
            'alternative_product_ids', result,
            "'alternative_product_ids' must be in the POS data fields."
        )

    def test_load_pos_data_fields_returns_list(self):
        """_load_pos_data_fields must return a list."""
        result = self.env['product.template']._load_pos_data_fields(
            self.pos_config.id)
        self.assertIsInstance(
            result, list,
            "_load_pos_data_fields must return a list."
        )

    def test_load_pos_data_fields_extends_parent_fields(self):
        """_load_pos_data_fields must extend the parent's field list (not
        replace it), so standard POS product fields are still present."""
        result = self.env['product.template']._load_pos_data_fields(
            self.pos_config.id)
        # The module adds 2 extra fields on top of the parent list
        self.assertGreater(
            len(result), 2,
            "_load_pos_data_fields must extend the parent list, not replace it."
        )
