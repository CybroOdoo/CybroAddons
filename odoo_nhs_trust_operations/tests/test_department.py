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
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import NhsOpsCommon


@tagged('post_install', '-at_install')
class TestDepartment(NhsOpsCommon):
    """nhs.trust.department: related trust, dissolved-trust guards, copy."""

    def test_trust_id_related_stored(self):
        """department.trust_id is the related (stored) site_id.trust_id."""
        self.assertEqual(self.dept.trust_id, self.trust_en)

    def test_cannot_create_department_under_dissolved_trust(self):
        """create() blocks departments under a dissolved trust."""
        self._force_state(self.trust_en, 'dissolved')
        with self.assertRaises(ValidationError):
            self.Dept.create({'name': 'Late Dept', 'site_id': self.site.id,
                              'department_type': 'support'})

    def test_cannot_modify_department_of_dissolved_trust(self):
        """write() blocks edits to a department whose trust is dissolved."""
        self._force_state(self.trust_en, 'dissolved')
        with self.assertRaises(ValidationError):
            self.dept.write({'staff_count': 10})

    def test_copy_name_is_formatted_string(self):
        """copy() yields a formatted '<name> (copy)' string, not a tuple."""
        clone = self.dept.copy()
        self.assertIsInstance(clone.name, str)
        self.assertEqual(clone.name, 'Emergency Department (copy)')
