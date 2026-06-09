# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aleena K (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase


class TestIndexAndFollow(TransactionCase):
    """Test cases for the Website Index and Follow module."""

    @classmethod
    def setUpClass(cls):
        super(TestIndexAndFollow, cls).setUpClass()
        cls.product = cls.env['product.template'].create({
            'name': 'Test Index Product',
            'list_price': 50.0,
        })

    def test_01_is_index_default_true(self):
        """Test that is_index defaults to True on a newly created product."""
        self.assertTrue(self.product.is_index,
                        "is_index should default to True.")

    def test_02_is_index_write_false(self):
        """Test that is_index can be set to False."""
        self.product.write({'is_index': False})
        self.assertFalse(self.product.is_index,
                         "is_index should be False after writing False.")

    def test_03_is_index_write_true(self):
        """Test that is_index can be set back to True."""
        self.product.write({'is_index': False})
        self.product.write({'is_index': True})
        self.assertTrue(self.product.is_index,
                        "is_index should be True after writing True.")