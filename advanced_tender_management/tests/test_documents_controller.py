# -*- coding: utf-8 -*-
import base64
from types import SimpleNamespace
from unittest.mock import patch

from odoo.http import Response

from odoo.addons.advanced_tender_management.controllers.documents import CustomFileDownloadController

from .common import TenderManagementTestCommon


class TestDocumentsController(TenderManagementTestCommon):
    """Tests for file download controller."""

    def test_download_file_returns_response_for_attachment(self):
        tender = self.create_tender()
        document = tender.tender_file_ids[:1]
        controller = CustomFileDownloadController()
        dummy_request = SimpleNamespace(
            env=self.env,
            not_found=lambda: 'not-found',
        )

        with patch('odoo.addons.advanced_tender_management.controllers.documents.request', dummy_request):
            response = controller.download_file(document.id)

        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, 200)
        self.assertIn(document.filename, response.headers.get('Content-Disposition'))
        self.assertEqual(response.data, base64.b64decode(document.attachment))

    def test_download_file_returns_not_found_without_attachment(self):
        controller = CustomFileDownloadController()
        dummy_request = SimpleNamespace(
            env=self.env,
            not_found=lambda: 'not-found',
        )

        with patch('odoo.addons.advanced_tender_management.controllers.documents.request', dummy_request):
            response = controller.download_file(999999)

        self.assertEqual(response, 'not-found')
