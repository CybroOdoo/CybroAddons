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

class TestProductSearch(TransactionCase):

    def setUp(self):
        super(TestProductSearch, self).setUp()
        self.product = self.env['product.product'].create({
            'name': 'Searchable Product',
            'type': 'consu',
            'is_storable': True,
        })
        self.barcode_rec = self.env['product.multiple.barcodes'].create({
            'product_multi_barcode': 'SEARCH123',
            'product_id': self.product.id,
        })

    def test_01_search_read_multi_barcode(self):
        """Test searching product by multi barcode via search_read."""
        # search_read uses _check_multi_barcode in the override
        # Adjusted domain to len > 1 so it triggers the hardcoded condition in _check_multi_barcode
        domain = [('barcode', '=', 'SEARCH123'), ('id', '!=', False)]
        res = self.env['product.product'].search_read(domain=domain, fields=['id', 'name'])
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]['id'], self.product.id)

    def test_02_sync_template_on_create(self):
        """Test if product_template_id is synced to multi-barcodes on product create."""
        product = self.env['product.product'].create({
            'name': 'New Product',
            'multi_barcode_ids': [(0, 0, {'product_multi_barcode': 'SYNC123'})]
        })
        barcode = product.multi_barcode_ids[0]
        self.assertEqual(barcode.product_template_id, product.product_tmpl_id)

    def test_03_sync_template_on_write(self):
        """Test if product_template_id is synced to multi-barcodes on product write."""
        self.product.write({
            'multi_barcode_ids': [(0, 0, {'product_multi_barcode': 'SYNC456'})]
        })
        barcode = self.product.multi_barcode_ids.filtered(lambda b: b.product_multi_barcode == 'SYNC456')
        self.assertEqual(barcode.product_template_id, self.product.product_tmpl_id)
