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
import io

import xlsxwriter

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tools import BinaryBytes

from .common import TenderManagementTestCommon


@tagged('post_install', '-at_install')
class TestImportTenderProductLine(TenderManagementTestCommon):
    """Tests for tender product import wizard."""

    def setUp(self):
        super().setUp()
        self.tender = self.create_tender()

    @staticmethod
    def _xlsx(rows):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        for row_index, row in enumerate(rows):
            for col_index, value in enumerate(row):
                sheet.write(row_index, col_index, value)
        workbook.close()
        return BinaryBytes(output.getvalue())

    def test_action_import_tender_product_lines_imports_rows(self):
        wizard = self.env['import.tender.product.line'].create({
            'file': self._xlsx([
                ['Product', 'Description', 'Qty'],
                ['Section Row'],
                [self.product_1.name, 'desc 1', 2],
                ['Brand New Product', 'desc 2', 4],
            ]),
            'tender_id': self.tender.id,
        })

        wizard.action_import_tender_product_lines()

        lines = self.tender.tender_product_line_ids
        self.assertTrue(lines.filtered(
            lambda line: line.display_type == 'line_section' and line.name == 'Section Row'))
        imported = lines.filtered(lambda line: line.name == 'desc 1')
        self.assertEqual(imported.product_id, self.product_1)
        self.assertEqual(imported.product_qty, 2)
        new_line = lines.filtered(lambda line: line.name == 'desc 2')
        self.assertEqual(new_line.product_id.name, 'Brand New Product')

    def test_export_then_import_round_trip(self):
        exported = BinaryBytes(self.tender._get_product_template_xlsx())
        other = self.create_tender(name='Copy', tender_product_line_ids=[])
        self.env['import.tender.product.line'].create({
            'file': exported, 'tender_id': other.id,
        }).action_import_tender_product_lines()
        self.assertEqual(other.tender_product_line_ids.product_id,
                         self.tender.tender_product_line_ids.product_id)

    def test_action_import_tender_product_lines_raises_on_invalid_file(self):
        wizard = self.env['import.tender.product.line'].create({
            'file': BinaryBytes(b'not an xlsx file'),
            'tender_id': self.tender.id,
        })

        with self.assertRaises(UserError):
            wizard.action_import_tender_product_lines()

    def test_import_rejects_non_numeric_quantity(self):
        wizard = self.env['import.tender.product.line'].create({
            'file': self._xlsx([
                ['Product', 'Description', 'Qty'],
                [self.product_1.name, 'desc 1', '5 pcs'],
            ]),
            'tender_id': self.tender.id,
        })
        lines_before = self.tender.tender_product_line_ids
        with self.assertRaisesRegex(UserError, 'Row 2'):
            wizard.action_import_tender_product_lines()
        self.assertEqual(self.tender.tender_product_line_ids, lines_before)

    def test_import_rejects_zero_and_negative_quantity(self):
        # 0.001 rounds to 0 at the default Product Unit precision (2 digits)
        for quantity in (0, -3, 0.001):
            wizard = self.env['import.tender.product.line'].create({
                'file': self._xlsx([
                    ['Product', 'Description', 'Qty'],
                    [self.product_1.name, 'desc 1', quantity],
                ]),
                'tender_id': self.tender.id,
            })
            with self.subTest(quantity=quantity), self.assertRaises(UserError):
                wizard.action_import_tender_product_lines()

    def test_import_accepts_decimal_text_and_empty_quantity(self):
        self.env['import.tender.product.line'].create({
            'file': self._xlsx([
                ['Product', 'Description', 'Qty'],
                [self.product_1.name, 'decimal qty', 2.5],
                [self.product_1.name, 'rounded qty', 1.23456],
                [self.product_1.name, 'text qty', '3.75'],
                [self.product_1.name, 'no qty'],
            ]),
            'tender_id': self.tender.id,
        }).action_import_tender_product_lines()
        lines = self.tender.tender_product_line_ids
        self.assertEqual(lines.filtered(lambda line: line.name == 'decimal qty').product_qty, 2.5)
        self.assertEqual(lines.filtered(lambda line: line.name == 'rounded qty').product_qty, 1.23)
        self.assertEqual(lines.filtered(lambda line: line.name == 'text qty').product_qty, 3.75)
        self.assertEqual(lines.filtered(lambda line: line.name == 'no qty').product_qty, 1)
