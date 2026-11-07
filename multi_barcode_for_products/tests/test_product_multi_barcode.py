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
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestProductMultiBarcode(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'is_storable': True,
            'barcode': 'MAIN123',
        })

    def test_01_create_multi_barcode(self):
        """Test if multi barcode is created properly."""
        self.env['product.multiple.barcodes'].create({
            'product_multi_barcode': 'ALT123',
            'product_id': self.product.id,
        })
        # Initial barcode MAIN123 + ALT123 = 2 barcodes
        self.assertEqual(len(self.product.multi_barcode_ids), 2)
        self.assertIn('ALT123', self.product.multi_barcode_ids.mapped('product_multi_barcode'))

    def test_02_barcode_unique_constraint(self):
        """Test the unique constraint on barcodes."""
        self.env['product.multiple.barcodes'].create({
            'product_multi_barcode': 'UNIQUE123',
            'product_id': self.product.id,
        })
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

    def test_04_onchanges(self):
        """Test _onchange_product_id and _onchange_product_template_id."""
        mb = self.env['product.multiple.barcodes'].new({'product_id': self.product.id})
        mb._onchange_product_id()
        self.assertEqual(mb.product_template_id, self.product.product_tmpl_id)

        mb2 = self.env['product.multiple.barcodes'].new({'product_template_id': self.product.product_tmpl_id.id})
        mb2._onchange_product_template_id()
        self.assertEqual(mb2.product_id, self.product)

    def test_05_sync_on_write_and_unlink(self):
        """Test syncing barcode to product on write and unlink."""
        prod = self.env['product.product'].create({'name': 'Sync Prod'})
        mb = self.env['product.multiple.barcodes'].create({
            'product_id': prod.id,
            'product_multi_barcode': 'SYNC1',
        })
        self.assertEqual(prod.barcode, 'SYNC1')
        mb.write({'product_multi_barcode': 'SYNC2'})
        self.assertEqual(prod.barcode, 'SYNC2')
        mb.unlink()
        self.assertFalse(prod.barcode)

    def test_06_find_product_by_barcode(self):
        """Test find_product_by_barcode across multi, variant, and template barcodes."""
        self.assertFalse(self.env['product.multiple.barcodes'].find_product_by_barcode(False))
        # Case insensitive multi-barcode search
        self.env['product.multiple.barcodes'].create({
            'product_id': self.product.id,
            'product_multi_barcode': 'CASETEST',
        })
        found = self.env['product.multiple.barcodes'].find_product_by_barcode('casetest')
        self.assertEqual(found, self.product)

        # Standard product barcode
        prod_std = self.env['product.product'].create({'name': 'Std Prod', 'barcode': 'STDBAR1'})
        found_std = self.env['product.multiple.barcodes'].find_product_by_barcode('STDBAR1')
        self.assertEqual(found_std, prod_std)
        found_std_lower = self.env['product.multiple.barcodes'].find_product_by_barcode('stdbar1')
        self.assertEqual(found_std_lower, prod_std)

        # Standard template barcode
        tmpl = self.env['product.template'].create({'name': 'Tmpl Bar', 'barcode': 'TMPLBAR1'})
        found_tmpl = self.env['product.multiple.barcodes'].find_product_by_barcode('TMPLBAR1')
        self.assertEqual(found_tmpl, tmpl.product_variant_id)

    def test_07_resolve_variant_template_only(self):
        """Test _resolve_product_variant when linked only via product_template_id."""
        tmpl = self.env['product.template'].create({'name': 'Tmpl Only'})
        mb = self.env['product.multiple.barcodes'].create({
            'product_template_id': tmpl.id,
            'product_multi_barcode': 'TMPLONLY1',
        })
        resolved = mb._resolve_product_variant()
        self.assertEqual(resolved, tmpl.product_variant_id)
