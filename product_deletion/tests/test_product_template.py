# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: ISMAIL C A (Contact : odoo@cybrosys.com)
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
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestProductTemplate(TransactionCase):
    """Test cases for product.template model."""

    @classmethod
    def setUpClass(cls):
        """Set up test records using existing users."""
        super().setUpClass()


        cls.group_product_deletion = cls.env.ref(
            'product_deletion.product_deletion_group_admin'
        )

        cls.user_without_access = (
            cls.env.ref('base.user_demo', raise_if_not_found=False)
            or cls.env.ref('base.default_user')
        )

        cls.user_with_access = cls.env.ref('base.user_admin')

        cls.product = cls.env['product.template'].create({
            'name': 'Test Product',
            'list_price': 100.0,
        })

    def setUp(self):
        """Configure user groups before each test."""
        super().setUp()

        self.user_without_access.write({
            'group_ids': [(3, self.group_product_deletion.id)]
        })

        self.user_with_access.write({
            'group_ids': [(4, self.group_product_deletion.id)]
        })

    def test_unlink_without_group(self):
        """User without group should not delete product."""

        with self.assertRaises(UserError):
            self.product.with_user(
                self.user_without_access
            ).unlink()

    def test_unlink_with_group(self):
        """User with group should delete product successfully."""

        product = self.env['product.template'].create({
            'name': 'Temporary Product',
            'list_price': 150.0,
        })

        product.with_user(
            self.user_with_access
        ).unlink()

        self.assertFalse(
            product.exists(),
            "Product should have been deleted successfully."
        )