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
from odoo.tests.common import TransactionCase

class TestPurchaseReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.report_model = cls.env['purchase.report']

    def test_select(self):
        """Test _select method returns SQL string containing brand_id"""
        select_query = self.report_model._select()
        self.assertTrue(hasattr(select_query, 'code'), "Should return SQL object")
        self.assertIn("t.brand_id AS brand_id", select_query.code)

    def test_group_by(self):
        """Test _group_by method returns SQL string containing brand_id"""
        group_by_query = self.report_model._group_by()
        self.assertTrue(hasattr(group_by_query, 'code'), "Should return SQL object")
        self.assertIn("t.brand_id", group_by_query.code)
