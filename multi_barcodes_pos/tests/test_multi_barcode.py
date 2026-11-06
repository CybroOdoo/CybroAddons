# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Gee Paul Joby (odoo@cybrosys.com)
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
from psycopg2 import IntegrityError

from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestMultiBarcodePos(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Product = self.env['product.product']
        self.MultiBarcode = self.env['multi.barcode.products']

        self.product_1 = self.Product.create({
            'name': 'Test Product 1',
            'barcode': '123456789'
        })

    def test_multi_barcode_creation(self):
        self.product_1.write({
            'product_multi_barcodes_ids': [
                Command.create({'multi_barcode': '987654321'})]
        })
        barcode_rec = self.product_1.product_multi_barcodes_ids.filtered(
            lambda b: b.multi_barcode == '987654321')

        self.assertEqual(barcode_rec.template_multi_id,
                         self.product_1.product_tmpl_id)

        self.product_1.product_tmpl_id.write({
            'template_multi_barcodes_ids': [
                Command.create({'multi_barcode': '111222333'})]
        })
        barcode_rec_2 = self.product_1.template_multi_barcodes_ids.filtered(
            lambda b: b.multi_barcode == '111222333')

        self.assertEqual(barcode_rec_2.product_multi_id, self.product_1)

    def test_barcode_uniqueness(self):
        self.MultiBarcode.create({
            'multi_barcode': 'DUP123',
            'product_multi_id': self.product_1.id,
            'template_multi_id': self.product_1.product_tmpl_id.id
        })

        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'):
            self.MultiBarcode.create({
                'multi_barcode': 'DUP123',
                'product_multi_id': self.product_1.id,
                'template_multi_id': self.product_1.product_tmpl_id.id
            })

    def test_get_barcode_val(self):
        barcode_val = 'SCAN789'
        self.product_1.write({
            'product_multi_barcodes_ids': [
                Command.create({'multi_barcode': barcode_val})]
        })

        res_barcode, res_product_id, res_tmpl_id = (
            self.MultiBarcode.get_barcode_val(barcode_val))

        self.assertEqual(res_barcode, barcode_val)
        self.assertEqual(res_product_id, self.product_1.id)
        self.assertEqual(res_tmpl_id, self.product_1.product_tmpl_id.id)

    def test_get_barcode_val_unknown(self):
        res_barcode, res_product_id, res_tmpl_id = (
            self.MultiBarcode.get_barcode_val('UNKNOWN000'))

        self.assertFalse(res_barcode)
        self.assertFalse(res_product_id)
        self.assertFalse(res_tmpl_id)

    def test_create_product_with_barcodes(self):
        product = self.Product.create({
            'name': 'Test Product 2',
            'product_multi_barcodes_ids': [
                Command.create({'multi_barcode': 'PRD001'})],
        })

        self.assertEqual(product.product_multi_barcodes_ids.template_multi_id,
                         product.product_tmpl_id)

    def test_create_template_with_barcodes(self):
        template = self.env['product.template'].create({
            'name': 'Test Template',
            'template_multi_barcodes_ids': [
                Command.create({'multi_barcode': 'TMPL001'})],
        })

        self.assertEqual(
            template.template_multi_barcodes_ids.product_multi_id,
            template.product_variant_id)

    def test_pos_data_loading(self):
        config = self.env['pos.config']

        models = self.env['pos.session']._load_pos_data_models(config)
        self.assertIn('multi.barcode.products', models)
        self.assertIn('product.product', models)

        fields = self.MultiBarcode._load_pos_data_fields(config)
        self.assertEqual(
            fields, ['multi_barcode', 'product_multi_id', 'template_multi_id'])
