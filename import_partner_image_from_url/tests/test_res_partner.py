# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests import common
import unittest.mock as mock

import base64

VALID_IMAGE_BYTES = base64.b64decode(b'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')

class TestResPartner(common.TransactionCase):

    def setUp(self):
        super(TestResPartner, self).setUp()
        self.Partner = self.env['res.partner']

    def test_download_image_from_url(self):
        """Test the _download_image_from_url method with valid and invalid responses."""
        partner = self.Partner.create({'name': 'Test Download'})
        
        with mock.patch('odoo.addons.import_partner_image_from_url.models.res_partner.requests.get') as mock_get:
            mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_response.headers = {'Content-Type': 'image/png'}
            mock_response.content = VALID_IMAGE_BYTES
            mock_get.return_value = mock_response
            
            result = partner._download_image_from_url('http://valid-url.com/image.png')
            self.assertTrue(result)
            
        with mock.patch('odoo.addons.import_partner_image_from_url.models.res_partner.requests.get') as mock_get:
            mock_response = mock.Mock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response
            
            with self.assertRaises(Exception):
                partner._download_image_from_url('http://invalid-url.com/image.png')
                
        with mock.patch('odoo.addons.import_partner_image_from_url.models.res_partner.requests.get') as mock_get:
            mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_response.headers = {'Content-Type': 'text/html'}
            mock_get.return_value = mock_response
            
            with self.assertRaises(Exception):
                partner._download_image_from_url('http://valid-url.com/not_image')

    def test_onchange_partner_image_url(self):
        """Test onchange method updates image."""
        partner = self.Partner.new({'name': 'Test Onchange', 'partner_image_url': 'http://valid-url.com/image.png'})
        
        with mock.patch('odoo.addons.import_partner_image_from_url.models.res_partner.requests.get') as mock_get:
            mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_response.headers = {'Content-Type': 'image/png'}
            mock_response.content = VALID_IMAGE_BYTES
            mock_get.return_value = mock_response
            
            partner._onchange_partner_image_url()
            self.assertTrue(partner.image_1920)

    def test_create(self):
        """Test create method sets image if url provided."""
        with mock.patch('odoo.addons.import_partner_image_from_url.models.res_partner.requests.get') as mock_get:
            mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_response.headers = {'Content-Type': 'image/png'}
            mock_response.content = VALID_IMAGE_BYTES
            mock_get.return_value = mock_response
            
            partner = self.Partner.create({
                'name': 'Test Create',
                'partner_image_url': 'http://valid-url.com/image.png'
            })
            self.assertTrue(partner.image_1920)

    def test_write(self):
        """Test write method updates image if url provided."""
        partner = self.Partner.create({'name': 'Test Write'})
        
        with mock.patch('odoo.addons.import_partner_image_from_url.models.res_partner.requests.get') as mock_get:
            mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_response.headers = {'Content-Type': 'image/png'}
            mock_response.content = VALID_IMAGE_BYTES
            mock_get.return_value = mock_response
            
            partner.write({'partner_image_url': 'http://valid-url.com/image.png'})
            self.assertTrue(partner.image_1920)
            
            partner.write({'partner_image_url': False})
            self.assertFalse(partner.image_1920)
