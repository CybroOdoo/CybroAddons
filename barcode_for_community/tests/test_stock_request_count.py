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

class TestStockRequestCount(TransactionCase):
    """Test suite for validating custom stock request count wizard logic."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment and classes."""
        super(TestStockRequestCount, cls).setUpClass()
        
    def test_get_values_to_write(self):
        """Test getting values to write for stock request count wizard"""
        # we check the returned dict from _get_values_to_write
        wizard = self.env['stock.request.count'].create({
            'set_count': 'set',
        })
        values = wizard._get_values_to_write()
        self.assertIsInstance(values, dict)
        self.assertTrue(values.get('created_custom_barcode', False))
        self.assertTrue(values.get('inventory_quantity_set', False))
