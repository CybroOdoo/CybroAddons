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
from types import SimpleNamespace
from unittest.mock import patch

from werkzeug.exceptions import NotFound

from odoo.addons.advanced_tender_management.controllers.documents import CustomFileDownloadController

from odoo.tests import tagged

from .common import TenderManagementTestCommon


@tagged('post_install', '-at_install')
class TestDocumentsController(TenderManagementTestCommon):
    """Tests for file download controller."""

    def _request(self):
        return SimpleNamespace(
            env=self.env,
            make_response=lambda data, headers=None: SimpleNamespace(
                data=data, headers=dict(headers or [])),
        )

    def test_download_file_returns_response_for_attachment(self):
        tender = self.create_tender(tender_state='bid_submission')
        document = tender.tender_file_ids[:1]
        controller = CustomFileDownloadController()

        with patch('odoo.addons.advanced_tender_management.controllers.documents.request',
                   self._request()):
            response = self.call_route(controller.download_file, document.id)

        self.assertIn(document.filename, response.headers['Content-Disposition'])
        self.assertEqual(response.headers['Content-Type'], 'text/plain')
        self.assertEqual(response.data, document.attachment.content)

    def test_download_file_of_draft_tender_is_not_found(self):
        document = self.create_tender().tender_file_ids[:1]
        with patch('odoo.addons.advanced_tender_management.controllers.documents.request',
                   self._request()):
            with self.assertRaises(NotFound):
                self.call_route(CustomFileDownloadController().download_file, document.id)

    def test_download_file_returns_not_found_without_attachment(self):
        controller = CustomFileDownloadController()

        with patch('odoo.addons.advanced_tender_management.controllers.documents.request',
                   self._request()):
            with self.assertRaises(NotFound):
                self.call_route(controller.download_file, 999999)
