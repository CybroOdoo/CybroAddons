# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPurchaseReport(TransactionCase):
    """Test cases for Purchase Report SQL extension"""

    def test_select(self):
        """Test the _select method includes brand_id."""
        report = self.env['purchase.report']
        select_query = str(report._select())
        self.assertIn('t.brand_id', select_query, "brand_id should be in the SELECT query")

    def test_group_by(self):
        """Test the _group_by method includes brand_id."""
        report = self.env['purchase.report']
        group_by_query = str(report._group_by())
        self.assertIn('t.brand_id', group_by_query, "brand_id should be in the GROUP BY query")
