# -*- coding: utf-8 -*-
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
import base64
import io
import openpyxl
from odoo.exceptions import UserError
from odoo.tests import tagged
from .common import MISSING_PATH, NOT_FOUND_URL, OK_URL, ProductImportCommon

HEADER = 'Product name,product type,Barcode,Price,Image'


@tagged('post_install', '-at_install')
class TestProductImportWizard(ProductImportCommon):
    """ CSV and XLSX import through the 'product.import' wizard """

    def setUp(self):
        super().setUp()
        self.image_path = self.make_image_file()
        self.existing = self.env['product.template'].create({
            'name': 'PI Existing',
            'list_price': 1.0,
        })

    def _wizard(self, option, raw_content):
        return self.env['product.import'].create({
            'option': option,
            'file': base64.b64encode(raw_content).decode(),
        })

    def _csv(self, *lines):
        return '\n'.join((HEADER,) + lines).encode('utf-8')

    def _xlsx(self, rows):
        book = openpyxl.Workbook()
        sheet = book.active
        sheet.append(HEADER.split(','))
        for row in rows:
            sheet.append(row)
        buffer = io.BytesIO()
        book.save(buffer)
        return buffer.getvalue()

    def _product(self, name):
        return self.env['product.template'].search([('name', '=', name)])

    def test_import_without_file(self):
        wizard = self.env['product.import'].create({'option': 'csv'})
        with self.assertRaisesRegex(UserError, 'Please upload a file'):
            wizard.import_file()

    def test_csv_import(self):
        content = self._csv(
            '',
            ',,,,',
            'PI Short,consu',
            'PI Shoes,consu,PI-BC-001,25.5,"%s"' % OK_URL,
            'PI Watch,consu,,,%s' % self.image_path,
            'PI Specs,service,PI-BC-003,10',
            'PI Existing,consu,PI-BC-004,99,%s' % OK_URL,
        )
        result = self._wizard('csv', content).import_file()

        self.assertIsNone(result)
        self.assertFalse(self._product('PI Short'))
        shoes = self._product('PI Shoes')
        self.assertEqual(shoes.type, 'consu')
        self.assertEqual(shoes.barcode, 'PI-BC-001')
        self.assertEqual(shoes.list_price, 25.5)
        self.assertTrue(shoes.image_1920)
        watch = self._product('PI Watch')
        self.assertFalse(watch.barcode)
        self.assertEqual(watch.list_price, 0.0)
        self.assertTrue(watch.image_1920)
        specs = self._product('PI Specs')
        self.assertEqual(specs.type, 'service')
        self.assertFalse(specs.image_1920)
        self.assertEqual(self.existing.barcode, 'PI-BC-004')
        self.assertEqual(self.existing.list_price, 99.0)
        self.assertTrue(self.existing.image_1920)
        self.assertEqual(len(self._product('PI Existing')), 1)

    def test_csv_import_image_failures(self):
        content = self._csv(
            'PI Bad URL,,PI-BC-011,1,%s' % NOT_FOUND_URL,
            'PI Bad Path,consu,PI-BC-012,2,%s' % MISSING_PATH,
            'PI Relative,consu,PI-BC-013,3,images/relative.png',
            'PI Existing,consu,,,',
        )
        result = self._wizard('csv', content).import_file()

        self.assertEqual(result['tag'], 'display_notification')
        self.assertEqual(result['params']['type'], 'warning')
        message = result['params']['message']
        self.assertIn('- PI Bad URL (%s): HTTP 404' % NOT_FOUND_URL, message)
        self.assertIn('- PI Bad Path (%s): file does not exist' % MISSING_PATH,
                      message)
        self.assertIn('- PI Relative (images/relative.png): not a web URL',
                      message)
        bad_url = self._product('PI Bad URL')
        self.assertEqual(bad_url.type, 'consu')
        self.assertFalse(bad_url.image_1920)
        self.assertTrue(self._product('PI Bad Path'))
        self.assertTrue(self._product('PI Relative'))
        self.assertFalse(self.existing.barcode)
        self.assertEqual(self.existing.list_price, 0.0)

    def test_csv_import_cp1252_file(self):
        content = (HEADER + '\nPI Café,consu,PI-BC-021,3\n').encode('cp1252')
        self._wizard('csv', content).import_file()
        self.assertTrue(self._product('PI Café'))

    def test_csv_import_latin1_fallback(self):
        """ Bytes invalid in both UTF-8 and cp1252 are read as latin-1 """
        content = HEADER.encode() + b'\nPI Latin\x81,consu,PI-BC-022,3\n'
        self._wizard('csv', content).import_file()
        self.assertTrue(self._product('PI Latin\x81'))

    def test_import_invalid_product_type(self):
        wizard = self._wizard('csv', self._csv('PI Bad Type,storable,,1'))
        with self.assertRaisesRegex(
                UserError, "Invalid product type 'storable' for product 'PI Bad Type'"):
            wizard.import_file()

    def test_import_invalid_price(self):
        wizard = self._wizard('csv', self._csv('PI Bad Price,consu,,ten'))
        with self.assertRaisesRegex(
                UserError, "Invalid price 'ten' for product 'PI Bad Price'"):
            wizard.import_file()

    def test_xlsx_import(self):
        content = self._xlsx([
            [None, 'consu', 'PI-BC-040', 1, None],
            ['PI X Shoes', 'consu', 5465465554, 25.5, OK_URL],
            ['PI X Watch', None, None, None, '  %s  ' % self.image_path],
            ['PI X Specs', 'service', 'PI-BC-043', 10, None],
            ['PI Existing', 'consu', 'PI-BC-044', 99, OK_URL],
        ])
        result = self._wizard('xlsx', content).import_file()

        self.assertIsNone(result)
        self.assertFalse(self.env['product.template'].search(
            [('barcode', '=', 'PI-BC-040')]))
        shoes = self._product('PI X Shoes')
        self.assertEqual(shoes.barcode, '5465465554')
        self.assertEqual(shoes.list_price, 25.5)
        self.assertTrue(shoes.image_1920)
        watch = self._product('PI X Watch')
        self.assertEqual(watch.type, 'consu')
        self.assertFalse(watch.barcode)
        self.assertEqual(watch.list_price, 0.0)
        self.assertTrue(watch.image_1920)
        self.assertEqual(self._product('PI X Specs').type, 'service')
        self.assertEqual(self.existing.barcode, 'PI-BC-044')
        self.assertEqual(self.existing.list_price, 99.0)
        self.assertTrue(self.existing.image_1920)

    def test_xlsx_import_image_failures(self):
        content = self._xlsx([
            ['PI X Bad URL', 'consu', 'PI-BC-051', 1, NOT_FOUND_URL],
            ['PI X Bad Path', 'consu', 'PI-BC-052', 2, MISSING_PATH],
            ['PI Existing', 'consu', None, None, None],
        ])
        result = self._wizard('xlsx', content).import_file()

        self.assertEqual(result['tag'], 'display_notification')
        message = result['params']['message']
        self.assertIn('- PI X Bad URL (%s): HTTP 404' % NOT_FOUND_URL, message)
        self.assertIn('- PI X Bad Path (%s)' % MISSING_PATH, message)
        self.assertFalse(self._product('PI X Bad URL').image_1920)
        self.assertFalse(self.existing.barcode)
        self.assertEqual(self.existing.list_price, 0.0)

    def test_xlsx_import_invalid_file(self):
        wizard = self._wizard('xlsx', b'this is not a spreadsheet')
        with self.assertRaisesRegex(UserError, 'Please choose the correct file'):
            wizard.import_file()
