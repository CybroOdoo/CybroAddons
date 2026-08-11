# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: AYANA KP (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests.common import TransactionCase
from psycopg2 import IntegrityError
from odoo.tools import mute_logger

class TestProductMultiBarcode(TransactionCase):

    def setUp(self):
        super(TestProductMultiBarcode, self).setUp()
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'is_storable': True,
            'barcode': 'MAIN123',
        })

    def test_01_create_multi_barcode(self):
        """Test if multi barcode is created properly."""
        self.env['product.multiple.barcodes'].create({
            'product_multi_barcode': 'ALT123',
            'product_id': self.product.id,
        })
        self.assertEqual(len(self.product.multi_barcode_ids), 1)

    def test_02_barcode_unique_constraint(self):
        """Test the unique constraint on barcodes."""
        self.env['product.multiple.barcodes'].create({
            'product_multi_barcode': 'UNIQUE123',
            'product_id': self.product.id,
        })
        from odoo.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.env['product.multiple.barcodes'].create({
                'product_multi_barcode': 'UNIQUE123',
                'product_id': self.product.id,
            })

    def test_03_get_barcode_val(self):
        """Test get_barcode_val method."""
        barcode_rec = self.env['product.multiple.barcodes'].create({
            'product_multi_barcode': 'VAL123',
            'product_id': self.product.id,
        })
        val, product = barcode_rec.get_barcode_val(self.product)
        self.assertEqual(val, 'VAL123')
        self.assertEqual(product, self.product)
