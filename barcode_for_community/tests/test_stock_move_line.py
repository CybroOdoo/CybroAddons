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

class TestStockMoveLine(TransactionCase):
    """Test suite for validating custom stock move line behavior and batch reading."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment and initialize test product and location."""
        super(TestStockMoveLine, cls).setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Test Move Line Product',
            'type': 'product'
        })
        cls.location = cls.env['stock.location'].create({'name': 'Loc', 'usage': 'internal'})

    def test_batch_read(self):
        """Testing batch read capability on stock move lines"""
        # Stub the batch read function
        res = self.env['stock.move.line'].search([]).batch_read(['id'])
        self.assertIsInstance(res, list)
