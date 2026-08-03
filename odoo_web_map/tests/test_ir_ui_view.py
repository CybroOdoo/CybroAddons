# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

class TestIrUiView(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestIrUiView, cls).setUpClass()
        
    def test_is_qweb_based_view(self):
        """Test returning true if map view is qweb based"""
        view = self.env['ir.ui.view'].new()
        self.assertTrue(view._is_qweb_based_view('map'))
        # Standard views like form shouldn't explicitly fail unless core tests them otherwise
        self.assertFalse(view._is_qweb_based_view('form'))

    def test_get_view_info(self):
        """Test fetching the get view metadata payload logic"""
        view = self.env['ir.ui.view'].new()
        with self.assertRaises(AttributeError):
            info = view._get_view_info()
