#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
# pylint: disable=missing-module-docstring,unknown-option-value,too-few-public-methods
"""Unit tests for Product Removal Authorisation module."""
import os

from odoo.exceptions import UserError
from odoo.modules.module import get_module_path
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'product_deletion')
class TestProductDeletion(TransactionCase):
    """Test suite verifying product removal authorization restrictions,
    group privileges, and module integrity.
    """

    @classmethod
    def setUpClass(cls):
        """Initialize test users and test products."""
        super().setUpClass()
        cls.module_path = get_module_path('product_deletion')
        cls.module = cls.env['ir.module.module'].search([
            ('name', '=', 'product_deletion'),
        ], limit=1)

        # Retrieve security groups
        cls.group_deletion = cls.env.ref(
            'product_deletion.product_deletion_group_admin',
        )
        cls.group_internal = cls.env.ref('base.group_user')

        # Create regular user without product deletion group
        cls.user_unauthorized = cls.env['res.users'].create({
            'name': 'Unauthorized User',
            'login': 'unauthorized_deletion_test_user',
            'email': 'unauth_deletion@gmail.com',
            'group_ids': [(6, 0, [cls.group_internal.id])],
        })

        # Create user with product deletion group
        cls.user_authorized = cls.env['res.users'].create({
            'name': 'Authorized User',
            'login': 'authorized_deletion_test_user',
            'email': 'auth_deletion@gmail.com',
            'group_ids': [(6, 0, [
                cls.group_internal.id,
                cls.group_deletion.id,
            ])],
        })

    def test_01_module_metadata(self):
        """Verify module installation state and manifest metadata."""
        self.assertTrue(self.module, "Module product_deletion must exist.")
        self.assertEqual(
            self.module.state, 'installed',
            "Module product_deletion should be installed.",
        )

    def test_02_unlink_unauthorized_user_raises_error(self):
        """Ensure an unauthorized user cannot delete a product template."""
        product = self.env['product.template'].create({
            'name': 'Test Restricted Product 1',
            'type': 'consu',
            'list_price': 50.0,
        })
        self.assertTrue(product.id)

        # Attempt to unlink with unauthorized user
        with self.assertRaises(UserError) as cm:
            product.with_user(self.user_unauthorized).unlink()

        self.assertIn(
            "You cannot delete the product(s)",
            str(cm.exception),
            "Expected specific user error message for unauthorized deletion.",
        )
        # Ensure product still exists in database
        self.assertTrue(
            product.exists(),
            "Product should not be deleted by unauthorized user.",
        )

    def test_03_unlink_authorized_user_succeeds(self):
        """Ensure an authorized user in the group can successfully delete."""
        product = self.env['product.template'].create({
            'name': 'Test Allowed Product 2',
            'type': 'consu',
            'list_price': 100.0,
        })
        self.assertTrue(product.id)

        # Unlink with authorized user
        res = product.with_user(self.user_authorized).unlink()
        self.assertTrue(res, "unlink should return True on success.")
        self.assertFalse(
            product.exists(),
            "Product should be deleted from the database.",
        )

    def test_04_unlink_superuser_succeeds(self):
        """Ensure superuser with deletion group can delete products."""
        # Ensure superuser has the group or test with superuser environment
        self.env.user.write({
            'group_ids': [(4, self.group_deletion.id)],
        })
        product = self.env['product.template'].create({
            'name': 'Test Superuser Product 3',
            'type': 'consu',
            'list_price': 25.0,
        })
        self.assertTrue(product.id)
        res = product.unlink()
        self.assertTrue(res)
        self.assertFalse(product.exists())

    def test_05_static_documentation_and_assets(self):
        """Verify presence and validity of documentation and icon assets."""
        self.assertTrue(
            self.module_path and os.path.isdir(self.module_path),
            "Module path must exist on disk.",
        )
        icon_path = os.path.join(
            self.module_path, 'static', 'description', 'icon.png',
        )
        self.assertTrue(os.path.isfile(icon_path), "icon.png must exist.")

        banner_path = os.path.join(
            self.module_path, 'static', 'description', 'banner.jpg',
        )
        self.assertTrue(os.path.isfile(banner_path), "banner.jpg must exist.")

        readme_path = os.path.join(self.module_path, 'README.rst')
        self.assertTrue(os.path.isfile(readme_path), "README.rst must exist.")

        release_notes_path = os.path.join(
            self.module_path, 'doc', 'RELEASE_NOTES.md',
        )
        self.assertTrue(
            os.path.isfile(release_notes_path),
            "RELEASE_NOTES.md must exist.",
        )

        index_path = os.path.join(
            self.module_path, 'static', 'description', 'index.html',
        )
        self.assertTrue(os.path.isfile(index_path), "index.html must exist.")
