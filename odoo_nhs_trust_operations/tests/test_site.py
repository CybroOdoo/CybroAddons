# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import NhsOpsCommon


@tagged('post_install', '-at_install')
class TestSite(NhsOpsCommon):
    """nhs.trust.site CRUD guards, copy and counts."""

    def test_department_count(self):
        """site.department_count reflects its departments."""
        self.assertEqual(self.site.department_count, 1)

    def test_cannot_create_site_under_dissolved_trust(self):
        """create() blocks sites under a dissolved trust."""
        self._force_state(self.trust_en, 'dissolved')
        with self.assertRaises(ValidationError):
            self.Site.create({'name': 'New Wing', 'trust_id': self.trust_en.id,
                              'site_type': 'clinic'})

    def test_cannot_modify_site_of_dissolved_trust(self):
        """write() blocks edits to a site whose trust is dissolved."""
        self._force_state(self.trust_en, 'dissolved')
        with self.assertRaises(ValidationError):
            self.site.write({'bed_capacity': 200})

    def test_unlink_blocked_when_departments_exist(self):
        """A site with departments cannot be deleted."""
        with self.assertRaises(UserError):
            self.site.unlink()

    def test_unlink_allowed_without_departments(self):
        """A site with no departments can be deleted."""
        empty = self.Site.create({'name': 'Empty Site', 'trust_id': self.trust_en.id,
                                   'site_type': 'admin_office'})
        empty.unlink()  # must not raise

    def test_copy_name_is_formatted_string(self):
        """copy() yields a properly formatted '<name> (copy)' string, not a tuple."""
        clone = self.site.copy()
        self.assertIsInstance(clone.name, str)
        self.assertEqual(clone.name, 'Royal London Hospital (copy)')
