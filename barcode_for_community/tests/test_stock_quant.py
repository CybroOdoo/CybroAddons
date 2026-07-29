# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase

class TestStockQuant(TransactionCase):
    """Test suite for validating custom stock quant field additions and logic."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment and initialize test product."""
        super(TestStockQuant, cls).setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Test Quant Product',
            'type': 'product'
        })
        cls.location = cls.env.ref('stock.stock_location_stock')

    def test_created_custom_barcode_field(self):
        """Test custom barcode field creation in stock_quant"""
        quant = self.env['stock.quant'].create({
            'product_id': self.product.id,
            'location_id': self.location.id,
            'inventory_quantity': 10,
            'created_custom_barcode': True
        })
        self.assertTrue(quant.created_custom_barcode)
