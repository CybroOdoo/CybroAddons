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
from odoo.exceptions import UserError
import unittest.mock as mock
import base64

class TestBulkPartnerImageImport(common.TransactionCase):

    def setUp(self):
        super(TestBulkPartnerImageImport, self).setUp()
        self.Wizard = self.env['bulk.partner.image.import']
        self.Partner = self.env['res.partner']

    def test_action_import_images_success(self):
        """Test successful import."""
        self.Partner.create({'name': 'Test Partner 1'})
        csv_data = b"name,partner_image_url\nTest Partner 1,http://valid-url.com/img1.png\n"
        b64_data = base64.b64encode(csv_data)
        
        wizard = self.Wizard.create({
            'file': b64_data,
            'filename': 'test.csv'
        })
        
        with mock.patch('odoo.addons.import_partner_image_from_url.wizard.bulk_partner_image_import.requests.get') as mock_get:
            mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_response.content = base64.b64decode(b'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')
            mock_get.return_value = mock_response
            
            wizard.action_import_images()
            
            partner1 = self.Partner.search([('name', '=', 'Test Partner 1')])
            self.assertTrue(partner1.image_1920)

    def test_action_import_images_no_file(self):
        """Test import without file raises UserError."""
        wizard = self.Wizard.create({})
        with self.assertRaises(UserError):
            wizard.action_import_images()

    def test_action_import_images_errors(self):
        """Test import with various errors."""
        self.Partner.create({'name': 'Duplicate Partner'})
        self.Partner.create({'name': 'Duplicate Partner'})
        
        csv_data = b"name,partner_image_url\n,http://missing-name.com\nDuplicate In CSV,http://valid.com\nDuplicate In CSV,http://valid2.com\nNot Found,http://valid.com\nDuplicate Partner,http://valid.com\n"
        b64_data = base64.b64encode(csv_data)
        
        wizard = self.Wizard.create({
            'file': b64_data,
            'filename': 'test.csv'
        })
        
        with self.assertRaises(UserError) as err:
            wizard.action_import_images()
            
        err_msg = str(err.exception)
        self.assertIn("Line 2: Missing name or image URL", err_msg)
        self.assertIn("Line 4: Duplicate partner 'Duplicate In CSV' in CSV", err_msg)
        self.assertIn("Line 5: Partner 'Not Found' not found", err_msg)
        self.assertIn("Line 6: Multiple partners found with name 'Duplicate Partner'", err_msg)
