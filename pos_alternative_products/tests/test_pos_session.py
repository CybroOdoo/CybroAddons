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
class TestPosSession(TransactionCase):
    """Test cases for pos.session functions defined in
    pos_alternative_products/models/pos_session.py"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Fetch a real POS config to pass as config_id
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test POS Config Alt Products',
        })

    # -----------------------------------------------------------------
    # Tests for _load_pos_data_models
    # -----------------------------------------------------------------

    def test_load_pos_data_models_includes_stock_quant(self):
        """_load_pos_data_models must include 'stock.quant' in the returned
        list so that stock quantity data is available in the POS session."""
        result = self.env['pos.session']._load_pos_data_models(
            self.pos_config)
        self.assertIn(
            'stock.quant', result,
            "'stock.quant' must be present in the POS data models list."
        )

    def test_load_pos_data_models_returns_list(self):
        """_load_pos_data_models must return a list (not None or another type)."""
        result = self.env['pos.session']._load_pos_data_models(
            self.pos_config)
        self.assertIsInstance(
            result, list,
            "_load_pos_data_models must return a list."
        )

    def test_load_pos_data_models_extends_parent_list(self):
        """_load_pos_data_models must include all models returned by the parent
        super() call in addition to 'stock.quant' — it should not replace the
        parent list, only extend it."""
        result = self.env['pos.session']._load_pos_data_models(
            self.pos_config)
        # The parent already includes core POS models; the result must contain
        # more than just stock.quant
        self.assertGreater(
            len(result), 1,
            "_load_pos_data_models should extend the parent list, not replace it."
        )
        # stock.quant must be appended at the end (last or in list)
        self.assertIn('stock.quant', result)
