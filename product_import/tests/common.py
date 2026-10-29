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
import os
import tempfile
from unittest.mock import MagicMock, patch
from PIL import Image
from odoo.addons.product_import.models import product_image_url_mixin
from odoo.tests.common import TransactionCase

OK_URL = 'https://images.example.com/ok.png'
NOT_FOUND_URL = 'https://images.example.com/missing.png'
MISSING_PATH = '/nonexistent/product_import/missing.png'


class ProductImportCommon(TransactionCase):
    """ Shared helpers: a small valid PNG in memory and on disk, and a fake
    image server so no test reaches the network """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        buffer = io.BytesIO()
        Image.new('RGB', (2, 2), color='red').save(buffer, format='PNG')
        cls.png_bytes = buffer.getvalue()
        cls.png_b64 = base64.b64encode(cls.png_bytes).decode()

    def setUp(self):
        super().setUp()
        self.http = MagicMock()
        self.http.request.side_effect = self._fake_request
        http_patcher = patch.object(product_image_url_mixin, '_HTTP', self.http)
        http_patcher.start()
        self.addCleanup(http_patcher.stop)

    def _fake_request(self, method, url, **kwargs):
        """ Serve the test PNG for OK_URL and a 404 for anything else """
        if url == OK_URL:
            return MagicMock(status=200, headers={'Content-Type': 'image/png'},
                             data=self.png_bytes)
        return MagicMock(status=404, headers={})

    def make_image_file(self):
        """ Write the test PNG to a temporary file and return its path """
        file_desc, path = tempfile.mkstemp(suffix='.png')
        with os.fdopen(file_desc, 'wb') as image_file:
            image_file.write(self.png_bytes)
        self.addCleanup(os.remove, path)
        return path
