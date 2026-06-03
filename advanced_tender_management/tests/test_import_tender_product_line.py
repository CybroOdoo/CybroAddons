# -*- coding: utf-8 -*-
import base64
from unittest.mock import Mock, patch

from odoo.exceptions import UserError

from .common import TenderManagementTestCommon


class TestImportTenderProductLine(TenderManagementTestCommon):
    """Tests for tender product import wizard."""

    def setUp(self):
        super().setUp()
        self.tender = self.create_tender()

    def test_action_import_tender_product_lines_imports_rows(self):
        wizard = self.env['import.tender.product.line'].create({
            'file': base64.b64encode(b'test'),
            'tender_id': self.tender.id,
        })
        sheet = Mock()
        sheet.nrows = 3
        sheet.row_values.side_effect = [
            ['header'],
            [self.product_1.name, 'desc 1', 2],
            ['Section Row', '', 0],
        ]
        book = Mock()
        book.sheets.return_value = [sheet]

        with patch(
            'odoo.addons.advanced_tender_management.wizard.import_tender_product_line.xlrd.open_workbook',
            return_value=book,
        ):
            wizard.action_import_tender_product_lines()

        self.assertTrue(
            self.tender.tender_product_line_ids.filtered(lambda line: line.display_type == 'line_section')
        )
        self.assertTrue(
            self.tender.tender_product_line_ids.filtered(lambda line: line.product_id == self.product_1)
        )

    def test_action_import_tender_product_lines_raises_on_invalid_file(self):
        wizard = self.env['import.tender.product.line'].create({
            'file': base64.b64encode(b'test'),
            'tender_id': self.tender.id,
        })

        with patch(
            'odoo.addons.advanced_tender_management.wizard.import_tender_product_line.xlrd.open_workbook',
            side_effect=Exception('bad file'),
        ):
            with self.assertRaises(UserError):
                wizard.action_import_tender_product_lines()
