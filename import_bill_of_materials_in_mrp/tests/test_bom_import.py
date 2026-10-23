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
import os
import zipfile
import zlib
from io import BytesIO
import openpyxl

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged
from odoo.addons.import_bill_of_materials_in_mrp.wizard.bom_import import (
    is_binary_file,
    _extract_file_content,
    _read_excel_rows,
    _read_csv_rows,
    _get_val,
    safe_get_file_bytes,
)

CSV_HEADER = [
    'Reference',
    'Finished products',
    'Product variant',
    'Quantity',
    'Unit of measure',
    'Material product',
    'Material product quantity',
    'Material product unit of measure',
]


@tagged('post_install', '-at_install')
class TestBomImport(TransactionCase):
    """Test suite covering the bom.import wizard and all helper functions."""

    @classmethod
    def setUpClass(cls):
        """Set up test data for finished products and components."""
        super().setUpClass()
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')

        # Create test finished product templates & variants
        cls.finished_tmpl1 = cls.env['product.template'].create({
            'name': 'Test Finished Desk',
            'type': 'consu',
            'uom_id': cls.uom_unit.id,
            'default_code': 'TEST_FP_01',
            'barcode': '880000000001',
        })
        cls.finished_prod1 = cls.finished_tmpl1.product_variant_id
        if not cls.finished_prod1.barcode:
            cls.finished_prod1.barcode = '880000000001'
        if not cls.finished_prod1.default_code:
            cls.finished_prod1.default_code = 'TEST_FP_01'

        cls.finished_tmpl2 = cls.env['product.template'].create({
            'name': 'Test Finished Drawer',
            'type': 'consu',
            'uom_id': cls.uom_unit.id,
            'default_code': 'TEST_FP_02',
            'barcode': '880000000002',
        })
        cls.finished_prod2 = cls.finished_tmpl2.product_variant_id
        if not cls.finished_prod2.barcode:
            cls.finished_prod2.barcode = '880000000002'
        if not cls.finished_prod2.default_code:
            cls.finished_prod2.default_code = 'TEST_FP_02'

        # Create test component product templates & variants
        cls.comp_tmpl1 = cls.env['product.template'].create({
            'name': 'Test Component Wood',
            'type': 'consu',
            'uom_id': cls.uom_unit.id,
            'default_code': 'TEST_COMP_01',
            'barcode': '880000000003',
        })
        cls.comp_prod1 = cls.comp_tmpl1.product_variant_id
        if not cls.comp_prod1.barcode:
            cls.comp_prod1.barcode = '880000000003'
        if not cls.comp_prod1.default_code:
            cls.comp_prod1.default_code = 'TEST_COMP_01'

        cls.comp_tmpl2 = cls.env['product.template'].create({
            'name': 'Test Component Screw',
            'type': 'consu',
            'uom_id': cls.uom_unit.id,
            'default_code': 'TEST_COMP_02',
            'barcode': '880000000004',
        })
        cls.comp_prod2 = cls.comp_tmpl2.product_variant_id
        if not cls.comp_prod2.barcode:
            cls.comp_prod2.barcode = '880000000004'
        if not cls.comp_prod2.default_code:
            cls.comp_prod2.default_code = 'TEST_COMP_02'

    def _create_csv_content(self, rows):
        """Helper to create UTF-8 CSV bytes from row lists."""
        lines = [','.join(str(cell) for cell in row) for row in rows]
        return '\n'.join(lines).encode('utf-8')

    def _create_xlsx_content(self, rows):
        """Helper to create openpyxl Excel bytes from row lists."""
        wb = openpyxl.Workbook()
        ws = wb.active
        for row in rows:
            ws.append(list(row))
        bio = BytesIO()
        wb.save(bio)
        return bio.getvalue()

    def _b64(self, data):
        """Helper to return base64 encoded string for Binary field in Odoo 20."""
        return base64.b64encode(data).decode('ascii')

    # -------------------------------------------------------------------------
    # Unit Tests for Helper Functions
    # -------------------------------------------------------------------------

    def test_01_is_binary_file(self):
        """Test is_binary_file detection for zip/excel signatures and text."""
        # Zip / OpenXML signature
        self.assertTrue(is_binary_file(b'PK\x03\x04\x14\x00'))
        # Legacy binary xls signature
        self.assertTrue(is_binary_file(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'))
        # Plain CSV text
        self.assertFalse(is_binary_file(b'Reference,Finished products,Quantity'))
        # Empty byte sequence
        self.assertFalse(is_binary_file(b''))

    def test_02_extract_file_content(self):
        """Test _extract_file_content with raw files, xlsx archives, and nested zip files."""
        # 1. Non-zip raw content
        raw_csv = b'Col1,Col2\nVal1,Val2'
        self.assertEqual(_extract_file_content(raw_csv), raw_csv)

        # 2. Zip archive mimicking an .xlsx file (containing xl/workbook.xml)
        bio_xlsx = BytesIO()
        with zipfile.ZipFile(bio_xlsx, 'w') as zf:
            zf.writestr('xl/workbook.xml', b'<xml>sheet</xml>')
            zf.writestr('xl/worksheets/sheet1.xml', b'<xml>data</xml>')
        xlsx_bytes = bio_xlsx.getvalue()
        self.assertEqual(_extract_file_content(xlsx_bytes), xlsx_bytes)

        # 3. Zip archive containing [Content_Types].xml
        bio_ct = BytesIO()
        with zipfile.ZipFile(bio_ct, 'w') as zf:
            zf.writestr('[Content_Types].xml', b'<xml>types</xml>')
        ct_bytes = bio_ct.getvalue()
        self.assertEqual(_extract_file_content(ct_bytes), ct_bytes)

        # 4. Zip archive wrapping a CSV file
        bio_zip_csv = BytesIO()
        with zipfile.ZipFile(bio_zip_csv, 'w') as zf:
            zf.writestr('__MACOSX/._inner.csv', b'meta')
            zf.writestr('inner.csv', b'Ref,Product\nBOM1,Desk')
        zip_csv_bytes = bio_zip_csv.getvalue()
        extracted = _extract_file_content(zip_csv_bytes)
        self.assertEqual(extracted, b'Ref,Product\nBOM1,Desk')

        # 5. Zip archive wrapping an arbitrary file fallback
        bio_zip_other = BytesIO()
        with zipfile.ZipFile(bio_zip_other, 'w') as zf:
            zf.writestr('data.txt', b'Line1,Line2')
        self.assertEqual(_extract_file_content(bio_zip_other.getvalue()), b'Line1,Line2')

    def test_03_safe_get_file_bytes(self):
        """Test safe_get_file_bytes across strings, base64, zlib, data URLs, and empty values."""
        # None and empty
        self.assertEqual(safe_get_file_bytes(None), b'')
        self.assertEqual(safe_get_file_bytes(''), b'')
        self.assertEqual(safe_get_file_bytes(b''), b'')

        # Raw bytes
        self.assertEqual(safe_get_file_bytes(b'raw content'), b'raw content')

        # Standard base64 string
        b64_str = base64.b64encode(b'decoded text').decode('ascii')
        self.assertEqual(safe_get_file_bytes(b64_str), b'decoded text')

        # Base64 with data URI prefix
        data_uri = 'data:text/csv;base64,' + b64_str
        self.assertEqual(safe_get_file_bytes(data_uri), b'decoded text')

        # Base64 string with missing padding
        unpadded = b64_str.rstrip('=')
        self.assertEqual(safe_get_file_bytes(unpadded), b'decoded text')

        # Zlib compressed bytes
        compressed = zlib.compress(b'compressed data string')
        self.assertEqual(safe_get_file_bytes(compressed), b'compressed data string')

        # Base64 encoded zlib compressed bytes
        b64_compressed = base64.b64encode(compressed).decode('ascii')
        self.assertEqual(safe_get_file_bytes(b64_compressed), b'compressed data string')

    def test_04_get_val(self):
        """Test _get_val helper for indexing, type conversions, and defaults."""
        row = ['  Ref01  ', 5.0, 3.25, None, '', '  clean\ufeff  ']
        # String stripped
        self.assertEqual(_get_val(row, 0), 'Ref01')
        # Float integer conversion
        self.assertEqual(_get_val(row, 1), '5')
        # Float decimal conversion
        self.assertEqual(_get_val(row, 2), '3.25')
        # None returns default
        self.assertEqual(_get_val(row, 3, default='N/A'), 'N/A')
        # Empty string returns default
        self.assertEqual(_get_val(row, 4, default='default_val'), 'default_val')
        # BOM and whitespace stripped
        self.assertEqual(_get_val(row, 5), 'clean')
        # Out-of-bounds index returns default
        self.assertEqual(_get_val(row, 10, default='fallback'), 'fallback')

    def test_05_read_csv_rows(self):
        """Test _read_csv_rows for UTF-8, BOM, UTF-16, Latin-1, and rejection of binary files."""
        # 1. Binary file rejection
        with self.assertRaises(ValueError):
            _read_csv_rows(b'PK\x03\x04\x00\x00')

        # 2. Standard UTF-8 CSV
        csv_utf8 = b'Col1,Col2\nVal1,Val2\n\n'
        rows = _read_csv_rows(csv_utf8)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], ['Col1', 'Col2'])
        self.assertEqual(rows[1], ['Val1', 'Val2'])

        # 3. UTF-8 with BOM
        csv_bom = b'\xef\xbb\xbfColA,ColB\nValA,ValB'
        rows_bom = _read_csv_rows(csv_bom)
        self.assertEqual(rows_bom[0], ['ColA', 'ColB'])

        # 4. UTF-16 with BOM (Little Endian)
        csv_u16 = 'Col1,Col2\nVal1,Val2'.encode('utf-16')
        rows_u16 = _read_csv_rows(csv_u16)
        self.assertEqual(rows_u16[0], ['Col1', 'Col2'])

        # 5. Latin1 encoded content
        csv_latin1 = 'Café,Naïve\n1,2'.encode('latin1')
        rows_latin = _read_csv_rows(csv_latin1)
        self.assertEqual(rows_latin[0], ['Café', 'Naïve'])

    def test_06_read_excel_rows(self):
        """Test _read_excel_rows reads openpyxl sheets and handles errors."""
        xlsx_bytes = self._create_xlsx_content([
            ['Header1', 'Header2'],
            ['Row1Col1', 42],
        ])
        rows = _read_excel_rows(xlsx_bytes)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0], 'Header1')
        self.assertEqual(rows[1][1], 42)

        # Corrupt bytes must raise ValueError
        with self.assertRaises(ValueError):
            _read_excel_rows(b'corrupted_not_an_excel_file')

    # -------------------------------------------------------------------------
    # Model Tests for bom.import Wizard
    # -------------------------------------------------------------------------

    def test_07_action_import_bom_no_file(self):
        """Verify wizard execution does nothing when file is empty."""
        wizard = self.env['bom.import'].create({
            'file_type': 'csv',
            'bom_type': 'mtp',
        })
        res = wizard.action_import_bom()
        self.assertFalse(res)

    def test_08_action_import_bom_empty_file_or_header_only(self):
        """Verify wizard raises UserError when file has only header or no data."""
        csv_header_only = self._create_csv_content([CSV_HEADER])
        wizard = self.env['bom.import'].create({
            'file_type': 'csv',
            'bom_type': 'mtp',
            'file': self._b64(csv_header_only),
        })
        with self.assertRaises(UserError) as cm:
            wizard.action_import_bom()
        self.assertIn("The file contains no data to import!", str(cm.exception))

    def test_09_action_import_bom_csv_basic(self):
        """Verify basic CSV import creates mrp.bom and mrp.bom.line and returns success action."""
        csv_bytes = self._create_csv_content([
            CSV_HEADER,
            ['BOM_TEST_BASIC', self.finished_tmpl1.name, self.finished_prod1.default_code, '2.0',
             self.uom_unit.name, self.comp_prod1.default_code, '5.0', self.uom_unit.name],
        ])
        wizard = self.env['bom.import'].create({
            'file_type': 'csv',
            'bom_type': 'mtp',
            'product_by': 'name',
            'product_variant_by': 'default_code',
            'file': self._b64(csv_bytes),
        })
        res = wizard.action_import_bom()
        self.assertEqual(res.get('res_model'), 'success.message')

        # Verify created BOM
        bom = self.env['mrp.bom'].search([('code', '=', 'BOM_TEST_BASIC')], limit=1)
        self.assertTrue(bom)
        self.assertEqual(bom.product_tmpl_id, self.finished_tmpl1)
        self.assertEqual(bom.product_id, self.finished_prod1)
        self.assertEqual(bom.product_qty, 2.0)
        self.assertEqual(bom.type, 'normal')
        self.assertEqual(bom.uom_id, self.uom_unit)

        # Verify created BOM line
        self.assertEqual(len(bom.bom_line_ids), 1)
        line = bom.bom_line_ids[0]
        self.assertEqual(line.product_id, self.comp_prod1)
        self.assertEqual(line.product_qty, 5.0)
        self.assertEqual(line.uom_id, self.uom_unit)

        # Verify success message record
        msg_rec = self.env['success.message'].browse(res['res_id'])
        self.assertIn('1 Records imported successfully', msg_rec.message)

    def test_10_action_import_bom_multi_line(self):
        """Verify CSV import with subsequent empty finished product attaches component lines."""
        csv_bytes = self._create_csv_content([
            CSV_HEADER,
            ['BOM_TEST_MULTI', self.finished_tmpl1.name, self.finished_prod1.default_code, '1.0',
             self.uom_unit.name, self.comp_prod1.default_code, '3.0', self.uom_unit.name],
            ['', '', '', '', '', self.comp_prod2.default_code, '4.0', self.uom_unit.name],
        ])
        wizard = self.env['bom.import'].create({
            'file_type': 'csv',
            'bom_type': 'mtp',
            'product_by': 'name',
            'product_variant_by': 'default_code',
            'file': self._b64(csv_bytes),
        })
        wizard.action_import_bom()

        bom = self.env['mrp.bom'].search([('code', '=', 'BOM_TEST_MULTI')], limit=1)
        self.assertTrue(bom)
        self.assertEqual(len(bom.bom_line_ids), 2)
        comp_ids = bom.bom_line_ids.mapped('product_id')
        self.assertIn(self.comp_prod1, comp_ids)
        self.assertIn(self.comp_prod2, comp_ids)

    def test_11_action_import_bom_kit(self):
        """Verify bom_type 'kit' creates a phantom BOM."""
        csv_bytes = self._create_csv_content([
            CSV_HEADER,
            ['BOM_TEST_KIT', self.finished_tmpl1.name, self.finished_prod1.default_code, '1.0',
             self.uom_unit.name, self.comp_prod1.default_code, '2.0', self.uom_unit.name],
        ])
        wizard = self.env['bom.import'].create({
            'file_type': 'csv',
            'bom_type': 'kit',
            'product_by': 'name',
            'product_variant_by': 'default_code',
            'file': self._b64(csv_bytes),
        })
        wizard.action_import_bom()

        bom = self.env['mrp.bom'].search([('code', '=', 'BOM_TEST_KIT')], limit=1)
        self.assertTrue(bom)
        self.assertEqual(bom.type, 'phantom')

    def test_12_action_import_bom_by_barcode(self):
        """Verify searching products and variants by barcode."""
        csv_bytes = self._create_csv_content([
            CSV_HEADER,
            ['BOM_TEST_BARCODE', self.finished_tmpl1.barcode, self.finished_prod1.barcode, '1.0',
             self.uom_unit.name, self.comp_prod1.barcode, '1.0', self.uom_unit.name],
        ])
        wizard = self.env['bom.import'].create({
            'file_type': 'csv',
            'bom_type': 'mtp',
            'product_by': 'barcode',
            'product_variant_by': 'barcode',
            'file': self._b64(csv_bytes),
        })
        wizard.action_import_bom()

        bom = self.env['mrp.bom'].search([('code', '=', 'BOM_TEST_BARCODE')], limit=1)
        self.assertTrue(bom)
        self.assertEqual(bom.product_tmpl_id, self.finished_tmpl1)
        self.assertEqual(bom.bom_line_ids.product_id, self.comp_prod1)

    def test_13_action_import_bom_by_default_code(self):
        """Verify searching products and variants by default_code."""
        csv_bytes = self._create_csv_content([
            CSV_HEADER,
            ['BOM_TEST_DEFCODE', self.finished_tmpl2.default_code,
             self.finished_prod2.default_code, '3.0',
             self.uom_unit.name, self.comp_prod2.default_code, '6.0', self.uom_unit.name],
        ])
        wizard = self.env['bom.import'].create({
            'file_type': 'csv',
            'bom_type': 'mtp',
            'product_by': 'default_code',
            'product_variant_by': 'default_code',
            'file': self._b64(csv_bytes),
        })
        wizard.action_import_bom()

        bom = self.env['mrp.bom'].search([('code', '=', 'BOM_TEST_DEFCODE')], limit=1)
        self.assertTrue(bom)
        self.assertEqual(bom.product_tmpl_id, self.finished_tmpl2)
        self.assertEqual(bom.bom_line_ids.product_id, self.comp_prod2)

    def test_14_action_import_bom_fallback_search(self):
        """Verify fallback search finds product/variant when primary field does not match."""
        csv_bytes = self._create_csv_content([
            CSV_HEADER,
            ['BOM_TEST_FALLBACK', self.finished_tmpl1.default_code,
             self.finished_prod1.barcode, '1.0',
             self.uom_unit.name, self.comp_prod1.name, '2.0', self.uom_unit.name],
        ])
        wizard = self.env['bom.import'].create({
            'file_type': 'csv',
            'bom_type': 'mtp',
            'product_by': 'name',
            'product_variant_by': 'default_code',
            'file': self._b64(csv_bytes),
        })
        wizard.action_import_bom()

        bom = self.env['mrp.bom'].search([('code', '=', 'BOM_TEST_FALLBACK')], limit=1)
        self.assertTrue(bom)
        self.assertEqual(bom.product_tmpl_id, self.finished_tmpl1)
        self.assertEqual(bom.bom_line_ids.product_id, self.comp_prod1)

    def test_15_action_import_bom_excel_format(self):
        """Verify importing Bill of Materials using Excel xlsx file."""
        xlsx_bytes = self._create_xlsx_content([
            CSV_HEADER,
            ['BOM_TEST_EXCEL', self.finished_tmpl1.name, self.finished_prod1.default_code, 4,
             self.uom_unit.name, self.comp_prod1.default_code, 8, self.uom_unit.name],
        ])
        wizard = self.env['bom.import'].create({
            'file_type': 'xls',
            'bom_type': 'mtp',
            'product_by': 'name',
            'product_variant_by': 'default_code',
            'file': self._b64(xlsx_bytes),
        })
        res = wizard.action_import_bom()
        self.assertEqual(res.get('res_model'), 'success.message')

        bom = self.env['mrp.bom'].search([('code', '=', 'BOM_TEST_EXCEL')], limit=1)
        self.assertTrue(bom)
        self.assertEqual(bom.product_qty, 4.0)
        self.assertEqual(bom.bom_line_ids.product_qty, 8.0)

    def test_16_action_import_bom_format_fallbacks(self):
        """Verify format auto-fallbacks: CSV uploaded as 'xls' and XLSX as 'csv'."""
        # 1. file_type='xls', but content is plain text CSV
        csv_bytes = self._create_csv_content([
            CSV_HEADER,
            ['BOM_FALLBACK_CSV', self.finished_tmpl1.name, self.finished_prod1.default_code, '1.0',
             self.uom_unit.name, self.comp_prod1.default_code, '1.0', self.uom_unit.name],
        ])
        wizard1 = self.env['bom.import'].create({
            'file_type': 'xls',
            'bom_type': 'mtp',
            'file': self._b64(csv_bytes),
        })
        wizard1.action_import_bom()
        self.assertTrue(self.env['mrp.bom'].search([('code', '=', 'BOM_FALLBACK_CSV')]))

        # 2. file_type='csv', but content is binary Excel
        xlsx_bytes = self._create_xlsx_content([
            CSV_HEADER,
            ['BOM_FALLBACK_XLS', self.finished_tmpl1.name, self.finished_prod1.default_code, '1.0',
             self.uom_unit.name, self.comp_prod1.default_code, '1.0', self.uom_unit.name],
        ])
        wizard2 = self.env['bom.import'].create({
            'file_type': 'csv',
            'bom_type': 'mtp',
            'file': self._b64(xlsx_bytes),
        })
        wizard2.action_import_bom()
        self.assertTrue(self.env['mrp.bom'].search([('code', '=', 'BOM_FALLBACK_XLS')]))

    def test_17_action_import_bom_corrupt_file_error(self):
        """Verify UserError is raised when file content is invalid and unparseable."""
        corrupt_data = b'\x00\x01\x02\x03\x04\x05'
        wizard = self.env['bom.import'].create({
            'file_type': 'xls',
            'bom_type': 'mtp',
            'file': self._b64(corrupt_data),
        })
        with self.assertRaises(UserError):
            wizard.action_import_bom()

    def test_18_action_import_bom_product_not_found(self):
        """Verify UserError is raised when finished product is not found in database."""
        csv_bytes = self._create_csv_content([
            CSV_HEADER,
            ['BOM_ERR_PROD', 'Non_Existent_Product_12345', '', '1.0',
             self.uom_unit.name, self.comp_prod1.default_code, '1.0', self.uom_unit.name],
        ])
        wizard = self.env['bom.import'].create({
            'file_type': 'csv',
            'bom_type': 'mtp',
            'file': self._b64(csv_bytes),
        })
        with self.assertRaises(UserError) as cm:
            wizard.action_import_bom()
        self.assertIn("Product template 'Non_Existent_Product_12345' not found!", str(cm.exception))

    def test_19_action_import_bom_material_not_found(self):
        """Verify UserError is raised when material product variant is not found."""
        csv_bytes = self._create_csv_content([
            CSV_HEADER,
            ['BOM_ERR_MAT', self.finished_tmpl1.name, self.finished_prod1.default_code, '1.0',
             self.uom_unit.name, 'Non_Existent_Material_54321', '1.0', self.uom_unit.name],
        ])
        wizard = self.env['bom.import'].create({
            'file_type': 'csv',
            'bom_type': 'mtp',
            'file': self._b64(csv_bytes),
        })
        with self.assertRaises(UserError) as cm:
            wizard.action_import_bom()
        expected_msg = (
            "Material product variant 'Non_Existent_Material_54321' not found!"
        )
        self.assertIn(expected_msg, str(cm.exception))

    def test_20_action_import_bom_quantity_fallbacks(self):
        """Verify invalid quantity strings fallback safely to 1.0."""
        csv_bytes = self._create_csv_content([
            CSV_HEADER,
            ['BOM_INVALID_QTY', self.finished_tmpl1.name, self.finished_prod1.default_code,
             'invalid_qty', self.uom_unit.name, self.comp_prod1.default_code,
             'invalid_mat_qty', self.uom_unit.name],
        ])
        wizard = self.env['bom.import'].create({
            'file_type': 'csv',
            'bom_type': 'mtp',
            'file': self._b64(csv_bytes),
        })
        wizard.action_import_bom()

        bom = self.env['mrp.bom'].search([('code', '=', 'BOM_INVALID_QTY')], limit=1)
        self.assertTrue(bom)
        self.assertEqual(bom.product_qty, 1.0)
        self.assertEqual(bom.bom_line_ids.product_qty, 1.0)

    def test_21_action_import_bom_uom_fallback(self):
        """Verify non-existent UoM name falls back to variant or template UoM."""
        csv_bytes = self._create_csv_content([
            CSV_HEADER,
            ['BOM_UOM_FALLBACK', self.finished_tmpl1.name, self.finished_prod1.default_code, '1.0',
             'Non_Existent_UOM_XYZ', self.comp_prod1.default_code, '2.0', 'Non_Existent_UOM_ABC'],
        ])
        wizard = self.env['bom.import'].create({
            'file_type': 'csv',
            'bom_type': 'mtp',
            'file': self._b64(csv_bytes),
        })
        wizard.action_import_bom()

        bom = self.env['mrp.bom'].search([('code', '=', 'BOM_UOM_FALLBACK')], limit=1)
        self.assertTrue(bom)
        self.assertEqual(bom.uom_id, self.finished_tmpl1.uom_id)
        self.assertEqual(bom.bom_line_ids.uom_id, self.comp_prod1.uom_id)

    def test_22_action_import_bom_from_sample_files(self):
        """Verify import using the actual static sample CSV and Excel files."""
        # Ensure all sample products exist in database
        sample_products = [
            ('Customizable Desk', 'FURN_0096'),
            ('CONS_25630', 'CONS_25630'),
            ('E-COM12', 'E-COM12'),
            ('Drawer Black', 'FURN_2100'),
            ('FURN_0789', 'FURN_0789'),
            ('CONS_89957', 'CONS_89957'),
        ]
        for name, code in sample_products:
            tmpl = self.env['product.template'].search([
                '|', ('name', '=', name), ('default_code', '=', code)
            ], limit=1)
            if not tmpl:
                tmpl = self.env['product.template'].create({
                    'name': name,
                    'default_code': code,
                    'type': 'consu',
                    'uom_id': self.uom_unit.id,
                })
            else:
                if not tmpl.name:
                    tmpl.name = name
                if not tmpl.default_code:
                    tmpl.default_code = code
            variant = tmpl.product_variant_id
            if variant:
                variant.default_code = code

        module_path = os.path.dirname(os.path.dirname(__file__))
        sample_dir = os.path.join(module_path, 'static', 'sample_files')
        csv_sample_path = os.path.join(sample_dir, 'import_bom_csv.csv')
        excel_sample_path = os.path.join(sample_dir, 'import_bom_excel.xlsx')

        # Test CSV Sample Import
        if os.path.exists(csv_sample_path):
            with open(csv_sample_path, 'rb') as f:
                csv_data = f.read()
            wizard_csv = self.env['bom.import'].create({
                'file_type': 'csv',
                'bom_type': 'mtp',
                'product_by': 'name',
                'product_variant_by': 'default_code',
                'file': self._b64(csv_data),
            })
            res_csv = wizard_csv.action_import_bom()
            self.assertEqual(res_csv.get('res_model'), 'success.message')

        # Test Excel Sample Import
        if os.path.exists(excel_sample_path):
            with open(excel_sample_path, 'rb') as f:
                excel_data = f.read()
            wizard_xls = self.env['bom.import'].create({
                'file_type': 'xls',
                'bom_type': 'mtp',
                'product_by': 'name',
                'product_variant_by': 'default_code',
                'file': self._b64(excel_data),
            })
            res_xls = wizard_xls.action_import_bom()
            self.assertEqual(res_xls.get('res_model'), 'success.message')

    def test_23_success_message_method(self):
        """Verify wizard.success_message method directly."""
        wizard = self.env['bom.import'].create({
            'file_type': 'csv',
            'bom_type': 'mtp',
        })
        action = wizard.success_message(7)
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'success.message')
        self.assertEqual(action.get('target'), 'new')
        msg = self.env['success.message'].browse(action['res_id'])
        self.assertEqual(msg.message, '7 Records imported successfully')
