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
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestProductSearch(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'name': 'Searchable Product',
            'is_storable': True,
        })
        self.barcode_rec = self.env['product.multiple.barcodes'].create({
            'product_multi_barcode': 'SEARCH123',
            'product_id': self.product.id,
        })

    def test_01_search_read_multi_barcode(self):
        """Test searching product by multi barcode via search_read."""
        domain = [('barcode', '=', 'SEARCH123')]
        res = self.env['product.product'].search_read(domain=domain, fields=['id', 'name'])
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]['id'], self.product.id)

    def test_02_sync_template_on_create(self):
        """Test if product_template_id is synced to multi-barcodes on product create."""
        product = self.env['product.product'].create({
            'name': 'New Product',
            'multi_barcode_ids': [(0, 0, {'product_multi_barcode': 'SYNC123'})],
        })
        barcode = product.multi_barcode_ids[0]
        self.assertEqual(barcode.product_template_id, product.product_tmpl_id)

    def test_03_sync_template_on_write(self):
        """Test if product_template_id is synced to multi-barcodes on product write."""
        self.product.write({
            'multi_barcode_ids': [(0, 0, {'product_multi_barcode': 'SYNC456'})],
        })
        barcode = self.product.multi_barcode_ids.filtered(lambda b: b.product_multi_barcode == 'SYNC456')
        self.assertEqual(barcode.product_template_id, self.product.product_tmpl_id)

    def test_04_template_multi_barcode_create_and_write(self):
        """Test creating and writing template with multi_barcodes."""
        tmpl = self.env['product.template'].create({
            'name': 'Tmpl With Multi',
            'template_multi_barcode_ids': [(0, 0, {'product_multi_barcode': 'TMPLCREATE1'})],
        })
        self.assertTrue(tmpl.template_multi_barcode_ids[0].product_id)
        tmpl.write({
            'template_multi_barcode_ids': [(0, 0, {'product_multi_barcode': 'TMPLWRITE1'})],
        })
        new_mb = tmpl.template_multi_barcode_ids.filtered(lambda b: b.product_multi_barcode == 'TMPLWRITE1')
        self.assertTrue(new_mb.product_id)
