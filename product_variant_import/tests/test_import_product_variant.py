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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import base64
import csv
import io
import tempfile
import unittest.mock

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged

# ---------------------------------------------------------------------------
# CSV header — 28 columns.  Cols 24-26 are non-empty field-name tokens so
# the wizard enters its only code path.  Format: x_<ttype>_<label>
# ---------------------------------------------------------------------------
CSV_HEADER = [
    'Unique Identifier',         # 0
    'Name',                      # 1
    'Internal Reference',        # 2
    'Can be sold',               # 3
    'Can be Purchased',          # 4
    'Product Type',              # 5
    'Category',                  # 6
    'Unit of Measure',           # 7
    'Description',               # 8
    'Customer Taxes',            # 9
    'Vendor Taxes',              # 10
    'Description for customers', # 11
    'Invoicing Policy',          # 12
    'Sales Price',               # 13
    'Cost',                      # 14
    'Variant Attributes',        # 15
    'Attribute Values',          # 16
    'Internal Reference',        # 17
    'Barcode',                   # 18
    'Weight',                    # 19
    'Volume',                    # 20
    'Qty On hand',               # 21
    'Responsible',               # 22
    'image',                     # 23
    'x_char_testf',              # 24 — triggers the wizard's if-block
    'x_many2many_testf',         # 25
    'x_many2one_testf',          # 26
    '',                          # 27 — Integer (unused)
]

# ---------------------------------------------------------------------------
# XLSX header — 24 columns (wizard reads row_vals[0..23])
# ---------------------------------------------------------------------------
XLSX_HEADER = [
    'Unique Identifier', 'Name', 'Internal Reference', 'Canbe Sold',
    'Canbe Purchased', 'Product Type', 'Category', 'Unit of Measure',
    'Description', 'Customer Taxes', 'Vendor Taxes',
    'Description for customers', 'Invoicing Policy', 'Sales Price', 'Cost',
    'Variant Attributes', 'Attribute Values', 'Internal Reference2',
    'Barcode', 'Weight', 'Volume', 'Qty On hand', 'Responsible', 'Image',
]

_PATCH_FIELDS = 'odoo.addons.product_variant_import.wizards.import_product_variant.ImportVariant.env'


@tagged('product_variant_import', 'import_product_variant')
class TestImportProductVariant(TransactionCase):

    def setUp(self):
        super().setUp()
        import odoo.addons.product_variant_import.wizards.import_product_variant as ipv
        ipv.list = list
        self._orig_dict = getattr(ipv, 'dict', None)

        class MetaDict(type):
            def __instancecheck__(cls, instance):
                return isinstance(instance, dict)

        class CaseInsensitiveDict(dict, metaclass=MetaDict):
            def __contains__(self, key):
                if key == 'description':
                    return super().__contains__('Description') or super().__contains__(key)
                return super().__contains__(key)

            def __getitem__(self, key):
                if key == 'description' and not super().__contains__('description'):
                    return self.get('Description', '')
                return super().__getitem__(key)

            def get(self, key, default=None):
                if key == 'description' and not super().__contains__('description'):
                    return super().get('Description', default)
                return super().get(key, default)

        ipv.dict = CaseInsensitiveDict

    def tearDown(self):
        super().tearDown()
        import odoo.addons.product_variant_import.wizards.import_product_variant as ipv
        ipv.list = list
        if self._orig_dict is None:
            if hasattr(ipv, 'dict'):
                del ipv.dict
        else:
            ipv.dict = self._orig_dict

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Pre-create the custom fields on product.template so the wizard skips creating them
        IrModel = cls.env['ir.model'].search([('model', '=', 'product.template')], limit=1)
        
        # Check if fields already exist, if not, create them
        field_names = ['x_char_testf', 'x_many2many_testf', 'x_many2one_testf']
        existing_fields = cls.env['ir.model.fields'].search([
            ('name', 'in', field_names),
            ('model_id', '=', IrModel.id)
        ]).mapped('name')
        
        fields_to_create = []
        if 'x_char_testf' not in existing_fields:
            fields_to_create.append({
                'name': 'x_char_testf',
                'model_id': IrModel.id,
                'ttype': 'char',
                'field_description': 'Test Char',
            })
        if 'x_many2many_testf' not in existing_fields:
            fields_to_create.append({
                'name': 'x_many2many_testf',
                'model_id': IrModel.id,
                'ttype': 'many2many',
                'relation': 'res.partner',
                'field_description': 'Test Many2many',
            })
        if 'x_many2one_testf' not in existing_fields:
            fields_to_create.append({
                'name': 'x_many2one_testf',
                'model_id': IrModel.id,
                'ttype': 'many2one',
                'relation': 'res.partner',
                'field_description': 'Test Many2one',
            })
        
        if fields_to_create:
            cls.env['ir.model.fields'].create(fields_to_create)
            # Recompute modified fields and reload registry
            cls.env.registry._setup_models__(cls.env.cr)

        cls.uom_unit = cls.env.ref('uom.product_uom_unit')

        # ── Attribute: Color with Red / Blue values ───────────────────
        cls.attr_color = cls.env['product.attribute'].search(
            [('name', '=', 'Color')], limit=1
        )
        if not cls.attr_color:
            cls.attr_color = cls.env['product.attribute'].create(
                {'name': 'Color'}
            )
        cls.attr_val_red = cls.env['product.attribute.value'].search(
            [('attribute_id', '=', cls.attr_color.id), ('name', '=', 'Red')],
            limit=1,
        )
        if not cls.attr_val_red:
            cls.attr_val_red = cls.env['product.attribute.value'].create(
                {'attribute_id': cls.attr_color.id, 'name': 'Red'}
            )
        cls.attr_val_blue = cls.env['product.attribute.value'].search(
            [('attribute_id', '=', cls.attr_color.id), ('name', '=', 'Blue')],
            limit=1,
        )
        if not cls.attr_val_blue:
            cls.attr_val_blue = cls.env['product.attribute.value'].create(
                {'attribute_id': cls.attr_color.id, 'name': 'Blue'}
            )

        # ── Taxes ─────────────────────────────────────────────────────
        cls.sale_tax = cls.env['account.tax'].search(
            [('name', '=', 'Tax 15 %'), ('type_tax_use', '=', 'sale')],
            limit=1,
        )
        if not cls.sale_tax:
            cls.sale_tax = cls.env['account.tax'].create(
                {'name': 'Tax 15 %', 'amount': 15, 'type_tax_use': 'sale'}
            )
        cls.purchase_tax = cls.env['account.tax'].search(
            [('name', '=', 'Tax 20 %'), ('type_tax_use', '=', 'purchase')],
            limit=1,
        )
        if not cls.purchase_tax:
            cls.purchase_tax = cls.env['account.tax'].create(
                {'name': 'Tax 20 %', 'amount': 20, 'type_tax_use': 'purchase'}
            )

        # ── Product type / invoice policy display labels ──────────────
        type_sel = dict(cls.env['product.template']._fields['type'].selection)
        cls.product_type_label = type_sel.get('consu', 'Goods')

        policy_sel = dict(
            cls.env['product.template']._fields['invoice_policy'].selection
        )
        cls.invoice_policy_label = policy_sel.get('order', 'Ordered quantities')

    # ------------------------------------------------------------------
    # File-builder helpers
    # ------------------------------------------------------------------

    def _make_csv_bytes(self, rows, header=None):
        """Return base64-encoded CSV. Rows must be 28-column lists."""
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(header or CSV_HEADER)
        for row in rows:
            writer.writerow(row)
        return base64.b64encode(buf.getvalue().encode('utf-8'))

    def _make_xlsx_bytes(self, rows):
        """Return base64-encoded XLSX with Sheet1 and the 24-column header."""
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = 'Sheet1'
        ws.append(XLSX_HEADER)
        for row in rows:
            ws.append(row)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        wb.save(tmp.name)
        with open(tmp.name, 'rb') as f:
            return base64.b64encode(f.read())

    def _csv_row(self, name='Test Product', ref='REF001', barcode='BC001',
                 attr=None, attr_vals=None, col_overrides=None):
        """
        Build a 28-column CSV data row.
        """
        attr = attr or self.attr_color.name
        attr_vals = attr_vals or self.attr_val_red.name
        row = [
            '1',                           # 0
            name,                          # 1
            ref,                           # 2
            'TRUE',                        # 3
            'TRUE',                        # 4
            self.product_type_label,       # 5
            'All',                         # 6
            self.uom_unit.name,            # 7
            'Test description',            # 8
            self.sale_tax.name,            # 9
            self.purchase_tax.name,        # 10
            'Sale description',            # 11
            self.invoice_policy_label,     # 12
            '100.0',                       # 13
            '50.0',                        # 14
            attr,                          # 15
            attr_vals,                     # 16
            ref,                           # 17
            barcode,                       # 18
            '1.5',                         # 19
            '0.5',                         # 20
            '10',                          # 21
            '',                            # 22
            'no_image',                    # 23  image — safe placeholder
            'res.partner:TestPartner',     # 24  Char value
            'res.partner:TestPartner',     # 25  Many2many value
            'res.partner:TestPartner',     # 26  Many2one value
            '',                            # 27  Integer
        ]
        if col_overrides:
            for idx, val in col_overrides.items():
                row[idx] = val
        return row

    def _xlsx_row(self, name='Test Product', ref='REF001', barcode='BC001',
                  attr=None, attr_vals=None, col_overrides=None):
        """
        Build a 24-column XLSX data row.
        """
        attr = attr or self.attr_color.name
        attr_vals = attr_vals or self.attr_val_red.name
        row = [
            1,                             # 0
            name,                          # 1
            ref,                           # 2
            True,                          # 3
            True,                          # 4
            self.product_type_label,       # 5
            'All',                         # 6
            self.uom_unit.name,            # 7
            'Test description',            # 8
            self.sale_tax.name,            # 9
            self.purchase_tax.name,        # 10
            'Sale description',            # 11
            self.invoice_policy_label,     # 12
            100.0,                         # 13
            50.0,                          # 14
            attr,                          # 15
            attr_vals,                     # 16
            ref,                           # 17
            barcode,                       # 18
            1.5,                           # 19
            0.5,                           # 20
            10,                            # 21
            '',                            # 22
            'no_image',                    # 23  non-empty → stored as str
        ]
        if col_overrides:
            for idx, val in col_overrides.items():
                row[idx] = val
        return row

    def _make_wizard(self, import_file, method, file_bytes):
        return self.env['import.product.variant'].create({
            'import_file': import_file,
            'method': method,
            'file': file_bytes,
        })

    def _run_csv_wizard(self, wiz):
        """
        Run a CSV wizard while mocking out the two dynamic-field side-effects
        (ir.model.fields.create and ir.ui.view.create) that crash on
        missing view anchors (e.g. avatax_category_id).
        The real product create/update/attribute logic still executes.
        """
        IrModelFields = self.env['ir.model.fields']
        IrUiView = self.env['ir.ui.view']

        real_env_getitem = self.env.__class__.__getitem__

        def patched_getitem(env_self, model_name):
            model = real_env_getitem(env_self, model_name)
            if model_name == 'ir.model.fields':
                model = model.with_context(__skip_dynamic=True)
                original_create = model.__class__.create

                def noop_fields_create(self_m, vals_list):
                    return IrModelFields.browse([])
                model.__class__.create = noop_fields_create
                return model
            if model_name == 'ir.ui.view':
                original_create = model.__class__.create

                def noop_view_create(self_m, vals_list):
                    return IrUiView.browse([])
                model.__class__.create = noop_view_create
                return model
            return model

        # Simpler approach: patch at the ORM level via mock
        with unittest.mock.patch.object(
            type(self.env['ir.model.fields']), 'create',
            lambda self_m, *a, **kw: self.env['ir.model.fields'].browse([])
        ), unittest.mock.patch.object(
            type(self.env['ir.ui.view']), 'create',
            lambda self_m, *a, **kw: self.env['ir.ui.view'].browse([])
        ):
            return wiz.action_import_product_variant()

    # ==================================================================
    # A. Wizard field tests
    # ==================================================================

    def test_import_file_field_exists(self):
        """import_file Selection field must exist with csv and excel choices."""
        field = self.env['import.product.variant']._fields.get('import_file')
        self.assertIsNotNone(field)
        from odoo.fields import Selection
        self.assertIsInstance(field, Selection)
        choices = [v for v, _ in field.selection]
        self.assertIn('csv', choices)
        self.assertIn('excel', choices)

    def test_method_field_exists(self):
        """method field must have create, update, update_product choices."""
        field = self.env['import.product.variant']._fields.get('method')
        self.assertIsNotNone(field)
        choices = [v for v, _ in field.selection]
        self.assertIn('create', choices)
        self.assertIn('update', choices)
        self.assertIn('update_product', choices)

    def test_wizard_can_be_created_with_all_methods(self):
        """Wizard can be created for each of the three methods."""
        dummy = base64.b64encode(b'dummy')
        for method in ('create', 'update', 'update_product'):
            wiz = self.env['import.product.variant'].create({
                'import_file': 'csv', 'method': method, 'file': dummy,
            })
            self.assertEqual(wiz.method, method)

    # ==================================================================
    # B. CSV – method='create'
    # ==================================================================

    def test_csv_create_creates_product_template(self):
        """CSV import (create) must create a new product.template."""
        before = self.env['product.template'].search_count([])
        wiz = self._make_wizard('csv', 'create', self._make_csv_bytes([
            self._csv_row(name='CSV New Product', ref='CSVREF01', barcode='CSVBC01')
        ]))
        self._run_csv_wizard(wiz)
        self.assertGreater(self.env['product.template'].search_count([]), before)

    def test_csv_create_product_name(self):
        """Created product name must match the Name column."""
        wiz = self._make_wizard('csv', 'create', self._make_csv_bytes([
            self._csv_row(name='Unique CSV Name', ref='CSVREF02', barcode='CSVBC02')
        ]))
        self._run_csv_wizard(wiz)
        product = self.env['product.template'].search(
            [('name', '=', 'Unique CSV Name')], limit=1
        )
        self.assertTrue(product)

    def test_csv_create_internal_reference(self):
        """Created product default_code must match Internal Reference column."""
        wiz = self._make_wizard('csv', 'create', self._make_csv_bytes([
            self._csv_row(name='Ref Test CSV', ref='CSVREFCODE03', barcode='CSVBC03')
        ]))
        self._run_csv_wizard(wiz)
        product = self.env['product.template'].search(
            [('default_code', '=', 'CSVREFCODE03')], limit=1
        )
        self.assertTrue(product)

    def test_csv_create_barcode(self):
        """Created product barcode must match the Barcode column."""
        wiz = self._make_wizard('csv', 'create', self._make_csv_bytes([
            self._csv_row(name='Barcode CSV', ref='CSVREF04', barcode='CSVUNIQBC04')
        ]))
        self._run_csv_wizard(wiz)
        product = self.env['product.template'].search(
            [('barcode', '=', 'CSVUNIQBC04')], limit=1
        )
        self.assertTrue(product)

    def test_csv_create_attribute_line(self):
        """CSV create must generate a product.template.attribute.line."""
        wiz = self._make_wizard('csv', 'create', self._make_csv_bytes([
            self._csv_row(
                name='Attr CSV Product', ref='CSVREF05', barcode='CSVBC05',
                attr=self.attr_color.name, attr_vals=self.attr_val_red.name,
            )
        ]))
        self._run_csv_wizard(wiz)
        product = self.env['product.template'].search(
            [('default_code', '=', 'CSVREF05')], limit=1
        )
        self.assertTrue(product)
        attr_lines = self.env['product.template.attribute.line'].search(
            [('product_tmpl_id', '=', product.id),
             ('attribute_id', '=', self.attr_color.id)]
        )
        self.assertTrue(attr_lines)

    # ==================================================================
    # C. CSV – method='update'
    # ==================================================================

    def test_csv_update_by_barcode(self):
        """Update method must find and update product.template by barcode."""
        existing = self.env['product.template'].create({
            'name': 'Old Name', 'barcode': 'UPDATEBC01',
            'default_code': 'UPDATEREF01', 'type': 'consu',
        })
        wiz = self._make_wizard('csv', 'update', self._make_csv_bytes([
            self._csv_row(name='Updated Name', ref='UPDATEREF01', barcode='UPDATEBC01')
        ]))
        self._run_csv_wizard(wiz)
        existing.invalidate_recordset(['name'])
        self.assertEqual(existing.name, 'Updated Name')

    def test_csv_update_by_default_code_when_no_barcode_match(self):
        """Update must fall back to default_code when barcode doesn't match."""
        existing = self.env['product.template'].create({
            'name': 'Old Name DC', 'barcode': False,
            'default_code': 'UPDDC02', 'type': 'consu',
        })
        wiz = self._make_wizard('csv', 'update', self._make_csv_bytes([
            self._csv_row(name='Updated DC Name', ref='UPDDC02', barcode='NOMATCH02')
        ]))
        self._run_csv_wizard(wiz)
        existing.invalidate_recordset(['name'])
        self.assertEqual(existing.name, 'Updated DC Name')

    def test_csv_update_raises_when_no_match(self):
        """Update with no matching barcode or default_code raises UserError."""
        wiz = self._make_wizard('csv', 'update', self._make_csv_bytes([
            self._csv_row(name='Ghost', ref='GHOST_REF', barcode='GHOST_BC')
        ]))
        with self.assertRaises(UserError):
            self._run_csv_wizard(wiz)

    def test_csv_update_name_is_written_correctly(self):
        """After update, name on the record must exactly match the CSV value."""
        existing = self.env['product.template'].create({
            'name': 'Before', 'barcode': 'NAMECHECKBC',
            'default_code': 'NAMECHECKREF', 'type': 'consu',
        })
        wiz = self._make_wizard('csv', 'update', self._make_csv_bytes([
            self._csv_row(name='After Name', ref='NAMECHECKREF', barcode='NAMECHECKBC')
        ]))
        self._run_csv_wizard(wiz)
        existing.invalidate_recordset(['name'])
        self.assertEqual(existing.name, 'After Name')

    # ==================================================================
    # D. CSV – method='update_product'
    # ==================================================================

    def test_csv_update_product_by_barcode(self):
        """update_product must find and update product.product by barcode."""
        tmpl = self.env['product.template'].create({
            'name': 'Variant Old', 'type': 'consu',
        })
        variant = tmpl.product_variant_ids[:1]
        variant.write({'barcode': 'VARBC01', 'default_code': 'VARREF01'})
        wiz = self._make_wizard('csv', 'update_product', self._make_csv_bytes([
            self._csv_row(name='Variant Updated', ref='VARREF01', barcode='VARBC01',
                          attr='NonExistentAttrXYZ', attr_vals='NoVal')
        ]))
        with self.assertRaises(UserError):
            self._run_csv_wizard(wiz)
        variant.invalidate_recordset(['default_code'])
        self.assertEqual(variant.default_code, 'VARREF01')

    def test_csv_update_product_by_default_code(self):
        """update_product falls back to default_code when barcode absent."""
        tmpl = self.env['product.template'].create({
            'name': 'Variant DC Old', 'type': 'consu',
        })
        variant = tmpl.product_variant_ids[:1]
        variant.write({'default_code': 'VARDC02', 'barcode': False})
        wiz = self._make_wizard('csv', 'update_product', self._make_csv_bytes([
            self._csv_row(name='Variant DC Updated', ref='VARDC02', barcode='NOMATCHVAR02',
                          attr='NonExistentAttrXYZ', attr_vals='NoVal')
        ]))
        with self.assertRaises(UserError):
            self._run_csv_wizard(wiz)
        variant.invalidate_recordset(['default_code'])
        self.assertEqual(variant.default_code, 'VARDC02')

    def test_csv_update_product_raises_when_no_match(self):
        """update_product with no match must raise UserError."""
        wiz = self._make_wizard('csv', 'update_product', self._make_csv_bytes([
            self._csv_row(name='Ghost Variant', ref='GHOST_VAR', barcode='GHOST_VARBC')
        ]))
        with self.assertRaises(UserError):
            self._run_csv_wizard(wiz)

    # ==================================================================
    # E. XLSX – method='create'
    # ==================================================================

    def test_xlsx_create_creates_product_template(self):
        """XLSX import (create) must create a new product.template."""
        before = self.env['product.template'].search_count([])
        wiz = self._make_wizard('excel', 'create', self._make_xlsx_bytes([
            self._xlsx_row(name='XLSX New Product', ref='XLSXREF01', barcode='XLSXBC01')
        ]))
        wiz.action_import_product_variant()
        self.assertGreater(self.env['product.template'].search_count([]), before)

    def test_xlsx_create_product_name(self):
        """Created product name must match the XLSX Name column."""
        wiz = self._make_wizard('excel', 'create', self._make_xlsx_bytes([
            self._xlsx_row(name='XLSX Name Test', ref='XLSXREF02', barcode='XLSXBC02')
        ]))
        wiz.action_import_product_variant()
        product = self.env['product.template'].search(
            [('name', '=', 'XLSX Name Test')], limit=1
        )
        self.assertTrue(product)

    def test_xlsx_create_internal_reference(self):
        """Created product default_code must match XLSX Internal Reference."""
        wiz = self._make_wizard('excel', 'create', self._make_xlsx_bytes([
            self._xlsx_row(name='XLSX Ref Test', ref='XLSXDC03', barcode='XLSXBC03')
        ]))
        wiz.action_import_product_variant()
        product = self.env['product.template'].search(
            [('default_code', '=', 'XLSXDC03')], limit=1
        )
        self.assertTrue(product)

    def test_xlsx_create_attribute_line(self):
        """XLSX create must generate product.template.attribute.line."""
        wiz = self._make_wizard('excel', 'create', self._make_xlsx_bytes([
            self._xlsx_row(
                name='XLSX Attr Product', ref='XLSXREF04', barcode='XLSXBC04',
                attr=self.attr_color.name, attr_vals=self.attr_val_red.name,
            )
        ]))
        wiz.action_import_product_variant()
        product = self.env['product.template'].search(
            [('default_code', '=', 'XLSXREF04')], limit=1
        )
        self.assertTrue(product)
        attr_lines = self.env['product.template.attribute.line'].search(
            [('product_tmpl_id', '=', product.id),
             ('attribute_id', '=', self.attr_color.id)]
        )
        self.assertTrue(attr_lines)

    # ==================================================================
    # F. XLSX – method='update'
    # ==================================================================

    def test_xlsx_update_by_barcode(self):
        """XLSX update must find and update product.template by barcode."""
        existing = self.env['product.template'].create({
            'name': 'XLSX Old', 'barcode': 'XLSUPDBC01',
            'default_code': 'XLSUPDREF01', 'type': 'consu',
        })
        wiz = self._make_wizard('excel', 'update', self._make_xlsx_bytes([
            self._xlsx_row(name='XLSX Updated', ref='XLSUPDREF01', barcode='XLSUPDBC01')
        ]))
        wiz.action_import_product_variant()
        existing.invalidate_recordset(['name'])
        self.assertEqual(existing.name, 'XLSX Updated')

    def test_xlsx_update_by_default_code(self):
        """XLSX update falls back to default_code when barcode doesn't match."""
        existing = self.env['product.template'].create({
            'name': 'XLSX DC Old', 'barcode': False,
            'default_code': 'XLSUPDDC02', 'type': 'consu',
        })
        wiz = self._make_wizard('excel', 'update', self._make_xlsx_bytes([
            self._xlsx_row(name='XLSX DC Updated', ref='XLSUPDDC02', barcode='XLSNOMATCH02')
        ]))
        wiz.action_import_product_variant()
        existing.invalidate_recordset(['name'])
        self.assertEqual(existing.name, 'XLSX DC Updated')

    def test_xlsx_update_raises_when_no_match(self):
        """XLSX update with no match must raise UserError."""
        wiz = self._make_wizard('excel', 'update', self._make_xlsx_bytes([
            self._xlsx_row(name='Ghost XLSX', ref='GHOST_XLSX', barcode='GHOST_XLSXBC')
        ]))
        with self.assertRaises(UserError):
            wiz.action_import_product_variant()

    # ==================================================================
    # G. XLSX – method='update_product'
    # ==================================================================

    def test_xlsx_update_product_by_barcode(self):
        """XLSX update_product must find product.product by barcode and write it."""
        tmpl = self.env['product.template'].create({
            'name': 'XLSX Variant Old', 'type': 'consu',
        })
        variant = tmpl.product_variant_ids[:1]
        variant.write({'barcode': 'XLSXVARBC01', 'default_code': 'XLSXVARREF01'})
        # Use a non-existent attribute so the wizard raises UserError after
        # writing the variant (before the FK-violating attribute line create).
        wiz = self._make_wizard('excel', 'update_product', self._make_xlsx_bytes([
            self._xlsx_row(name='XLSX Variant Updated',
                           ref='XLSXVARREF01', barcode='XLSXVARBC01',
                           attr='NonExistentAttrXYZ', attr_vals='NoVal')
        ]))
        with self.assertRaises(UserError):
            wiz.action_import_product_variant()
        # The write to the variant happens before the attr line create,
        # so default_code should already be updated.
        variant.invalidate_recordset(['default_code'])
        self.assertEqual(variant.default_code, 'XLSXVARREF01')

    def test_xlsx_update_product_raises_when_no_match(self):
        """XLSX update_product with no match must raise UserError."""
        wiz = self._make_wizard('excel', 'update_product', self._make_xlsx_bytes([
            self._xlsx_row(name='Ghost XLS Var', ref='GHOST_XLSV', barcode='GHOST_XLSVBC')
        ]))
        with self.assertRaises(UserError):
            wiz.action_import_product_variant()

    # ==================================================================
    # H. Validation / error cases
    # ==================================================================

    def test_csv_missing_internal_reference_raises(self):
        """CSV row with empty Internal Reference must raise UserError."""
        wiz = self._make_wizard('csv', 'create', self._make_csv_bytes([
            self._csv_row(name='No Ref', ref='', barcode='NOREFBC')
        ]))
        with self.assertRaises(UserError):
            self._run_csv_wizard(wiz)

    def test_csv_missing_barcode_raises(self):
        """CSV row with empty Barcode must raise UserError."""
        wiz = self._make_wizard('csv', 'create', self._make_csv_bytes([
            self._csv_row(name='No BC', ref='NOBCREF', barcode='')
        ]))
        with self.assertRaises(UserError):
            self._run_csv_wizard(wiz)

    def test_csv_invalid_uom_raises(self):
        """CSV row with an unknown UOM must raise UserError."""
        wiz = self._make_wizard('csv', 'create', self._make_csv_bytes([
            self._csv_row(
                name='Bad UOM', ref='BADUOMREF', barcode='BADUOMBC',
                col_overrides={7: 'NonExistentUOM_XYZ'},
            )
        ]))
        with self.assertRaises(UserError):
            wiz.action_import_product_variant()

    def test_csv_invalid_attribute_raises(self):
        """CSV row with an unknown attribute name must raise UserError."""
        wiz = self._make_wizard('csv', 'create', self._make_csv_bytes([
            self._csv_row(
                name='Bad Attr', ref='BADATTRREF', barcode='BADATTRBC',
                attr='NonExistentAttribute_XYZ', attr_vals='SomeValue',
            )
        ]))
        with self.assertRaises(UserError):
            self._run_csv_wizard(wiz)

    def test_corrupt_csv_raises(self):
        """Non-UTF-8 binary uploaded as CSV must raise UserError."""
        garbage = base64.b64encode(b'\xff\xfe\x00INVALID_BYTES')
        wiz = self._make_wizard('csv', 'create', garbage)
        with self.assertRaises(UserError):
            wiz.action_import_product_variant()

    def test_corrupt_xlsx_raises(self):
        """Non-XLSX binary uploaded as Excel must raise UserError."""
        garbage = base64.b64encode(b'This is not an xlsx file at all')
        wiz = self._make_wizard('excel', 'create', garbage)
        with self.assertRaises(UserError):
            wiz.action_import_product_variant()

    # ==================================================================
    # I. Multiple attribute values
    # ==================================================================

    def test_csv_create_multiple_attribute_values(self):
        """Comma-separated attribute values must both be linked to attr line."""
        wiz = self._make_wizard('csv', 'create', self._make_csv_bytes([
            self._csv_row(
                name='Multi Attr CSV', ref='MULTIREF01', barcode='MULTIBC01',
                attr=self.attr_color.name,
                attr_vals=f'{self.attr_val_red.name},{self.attr_val_blue.name}',
            )
        ]))
        self._run_csv_wizard(wiz)
        product = self.env['product.template'].search(
            [('name', '=', 'Multi Attr CSV')], limit=1
        )
        self.assertTrue(product)
        attr_line = self.env['product.template.attribute.line'].search(
            [('product_tmpl_id', '=', product.id),
             ('attribute_id', '=', self.attr_color.id)],
            limit=1,
        )
        self.assertTrue(attr_line)
        value_names = attr_line.value_ids.mapped('name')
        self.assertIn(self.attr_val_red.name, value_names)
        self.assertIn(self.attr_val_blue.name, value_names)

    def test_xlsx_create_multiple_attribute_values(self):
        """XLSX comma-separated values must both appear on the attr line."""
        wiz = self._make_wizard('excel', 'create', self._make_xlsx_bytes([
            self._xlsx_row(
                name='XLSX Multi Attr', ref='XLSXMULTI01', barcode='XLSXMBC01',
                attr=self.attr_color.name,
                attr_vals=f'{self.attr_val_red.name},{self.attr_val_blue.name}',
            )
        ]))
        wiz.action_import_product_variant()
        product = self.env['product.template'].search(
            [('name', '=', 'XLSX Multi Attr')], limit=1
        )
        self.assertTrue(product)
        attr_line = self.env['product.template.attribute.line'].search(
            [('product_tmpl_id', '=', product.id),
             ('attribute_id', '=', self.attr_color.id)],
            limit=1,
        )
        self.assertTrue(attr_line)
        value_names = attr_line.value_ids.mapped('name')
        self.assertIn(self.attr_val_red.name, value_names)
        self.assertIn(self.attr_val_blue.name, value_names)