# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Fansa Jabeen A (odoo@cybrosys.com)
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
################################################################################
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestStockMoveBarcode(TransactionCase):
    """Test cases for stock.move barcode scanning."""

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'name': 'Test Stock Product',
            'barcode': 'stock_prod_123',
        })
        self.picking_type = self.env['stock.picking.type'].search([], limit=1)
        self.location = self.env['stock.location'].search(
            [('usage', '=', 'internal')], limit=1
        )
        self.location_dest = self.env['stock.location'].search(
            [('usage', '=', 'customer')], limit=1
        )
        self.picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type.id,
            'location_id': self.location.id,
            'location_dest_id': self.location_dest.id,
        })

    def test_onchange_barcode_scan(self):
        """Test _onchange_barcode_scan method directly."""
        line = self.env['stock.move'].new({
            'picking_id': self.picking.id,
            'location_id': self.location.id,
            'location_dest_id': self.location_dest.id,
            'barcode_scan': 'stock_prod_123',
        })
        self.assertFalse(line.product_id)
        line._onchange_barcode_scan()
        self.assertEqual(line.product_id, self.product)

    def test_onchange_barcode_scan_invalid(self):
        """Test _onchange_barcode_scan with non-existent barcode."""
        line = self.env['stock.move'].new({
            'picking_id': self.picking.id,
            'location_id': self.location.id,
            'location_dest_id': self.location_dest.id,
            'barcode_scan': 'non_existent_barcode',
        })
        line._onchange_barcode_scan()
        self.assertFalse(line.product_id)
