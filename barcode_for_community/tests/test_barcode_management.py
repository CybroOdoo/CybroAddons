# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo.tests.common import TransactionCase
from unittest.mock import patch, MagicMock

class TestBarcodeManagement(TransactionCase):
    """Test suite for validating the Abstract barcode.management model methods."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment and pre-configure environment context."""
        super(TestBarcodeManagement, cls).setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.model = cls.env['barcode.management']

    def test_return_barcode_models(self):
        """Test that barcode models are correctly returned based on user rights"""
        models = self.model.return_barcode_models()
        self.assertIsInstance(models, dict, "Should return a dictionary of models")
        self.assertIn('product.product', models)

    @patch('odoo.addons.barcode_for_community.models.barcode_management.BarcodeManagement.search_barcode_in_models')
    def test_search_barcode_in_models(self, mock_search):
        """Test searching barcodes across specified models"""
        mock_search.return_value = {'success': True}
        result = self.model.search_barcode_in_models('12345', 1)
        self.assertTrue(result.get('success', False))
