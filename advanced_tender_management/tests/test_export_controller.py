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
from types import SimpleNamespace
from unittest.mock import patch

from openpyxl import load_workbook
from werkzeug.exceptions import NotFound

from odoo.tests import tagged

from odoo.addons.advanced_tender_management.controllers.export import TenderExportController

from .common import TenderManagementTestCommon


@tagged('post_install', '-at_install')
class TestExportController(TenderManagementTestCommon):
    """Tests for the XLSX product template download."""

    def _request(self):
        return SimpleNamespace(
            env=self.env,
            make_response=lambda data, headers=None: SimpleNamespace(
                data=data, headers=dict(headers or [])),
        )

    def test_download_product_template(self):
        tender = self.create_tender()
        with patch('odoo.addons.advanced_tender_management.controllers.export.request',
                   self._request()):
            response = self.call_route(TenderExportController().download_product_template, tender.id)

        self.assertIn('Products.xlsx', response.headers['Content-Disposition'])
        sheet = load_workbook(io.BytesIO(response.data)).active
        rows = list(sheet.iter_rows(values_only=True))
        self.assertEqual(rows[0][:3], ('Product', 'Description', 'Qty'))
        self.assertEqual(rows[1][0], self.product_1.name)
        self.assertEqual(rows[1][2], 3)

    def test_download_unknown_tender(self):
        with patch('odoo.addons.advanced_tender_management.controllers.export.request',
                   self._request()):
            with self.assertRaises(NotFound):
                self.call_route(TenderExportController().download_product_template, 999999)

    def test_action_print_xlsx_report_points_to_download(self):
        tender = self.create_tender()
        action = tender.action_print_xlsx_report()
        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertEqual(action['url'], f'/tender/{tender.id}/product_template')
