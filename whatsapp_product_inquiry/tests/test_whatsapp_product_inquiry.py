# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:ISMAIL C A(odoo@cybrosys.com)
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

###############################################################################
from urllib.parse import quote_plus
from unittest.mock import patch, MagicMock
from odoo.tests import TransactionCase, tagged
from odoo.addons.whatsapp_product_inquiry.controllers.whatsapp_product_inquiry import WebsiteSale
import odoo.addons.whatsapp_product_inquiry.controllers.whatsapp_product_inquiry as controller_module


@tagged('post_install', '-at_install')
class TestWhatsappProductInquiry(TransactionCase):

    def setUp(self):
        super(TestWhatsappProductInquiry, self).setUp()
        self.company = self.env['res.company'].create({
            'name': 'Test Company',
            'whatsapp_number': '1234567890',
            'message': 'Hello Test',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
        })
        self.controller = WebsiteSale()

    def test_whatsapp_product_inquiry(self):
        """Test the whatsapp_product_inquiry controller method."""
        old_request = controller_module.request
        mock_request = MagicMock()
        controller_module.request = mock_request
        try:
            mock_website = MagicMock()
            mock_website.company_id = self.company
            mock_website.get_base_url.return_value = 'http://localhost:8069'
            mock_request.website.get_current_website.return_value = mock_website
            mock_request.website.get_base_url.return_value = 'http://localhost:8069'
            
            mock_env = MagicMock()
            mock_product_record = MagicMock()
            mock_product_record.website_url = f'/shop/product/{self.product.id}'
            mock_env['product.product'].browse.return_value = mock_product_record
            mock_request.env = mock_env

            result = self.controller.whatsapp_product_inquiry(self.product.id)

            expected_message = self.company.message + '\nProduct Url: http://localhost:8069/shop/product/' + str(self.product.id)
            encoded_message = quote_plus(expected_message)
            expected_url = f"https://wa.me/{self.company.whatsapp_number}?text={encoded_message}"

            self.assertEqual(result.location, expected_url)
        finally:
            controller_module.request = old_request
