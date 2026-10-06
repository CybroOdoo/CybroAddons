# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo.tests.common import HttpCase
from unittest.mock import patch, MagicMock

class TestAllInOnePurchaseKitController(HttpCase):

    def setUp(self):
        super().setUp()

    def test_get_report_xlsx(self):
        """Test the XLSX report controller endpoint"""
        from odoo.addons.all_in_one_purchase_kit.controllers import all_in_one_purchase_kit
        
        controller = all_in_one_purchase_kit.TBXLSXReportController()
        
        # Save original request to restore later
        original_request = getattr(all_in_one_purchase_kit, 'request', None)
        
        try:
            # Manually patch request
            mock_request = MagicMock()
            mock_request.session.uid = self.env.user.id
            mock_request.env = self.env
            mock_response = MagicMock()
            mock_request.make_response.return_value = mock_response
            all_in_one_purchase_kit.request = mock_request
            
            # Mock the method that gets called
            with patch('odoo.addons.all_in_one_purchase_kit.models.dynamic_purchase_report.DynamicPurchaseReport.get_purchase_xlsx_report') as mock_method:
                
                # Use __wrapped__ to bypass the @route decorator
                result = controller.get_report_xlsx.__wrapped__(
                    controller,
                    model='dynamic.purchase.report',
                    options={},
                    output_format='xlsx',
                    report_data='[]',
                    report_name='test_report',
                    dfr_data={}
                )
                
                self.assertTrue(mock_method.called)
                self.assertEqual(result, mock_response)
        finally:
            if original_request:
                all_in_one_purchase_kit.request = original_request
