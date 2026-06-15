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
import psycopg2
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import NhsOpsCommon


@tagged('post_install', '-at_install')
class TestSpecialty(NhsOpsCommon):
    """nhs.trust.specialty uniqueness (DB Constraint) and copy."""

    # NOTE: Odoo's assertRaises override accepts a single exception class only
    # (not a tuple). The DB unique Constraint fires at flush as IntegrityError.
    @mute_logger('odoo.sql_db')
    def test_duplicate_name_rejected(self):
        """A duplicate specialty name is rejected by the unique constraint."""
        with self.assertRaises(psycopg2.IntegrityError):
            with self.cr.savepoint():
                self.Specialty.create({'name': 'Cardiology', 'code': '999'})
                self.env.flush_all()

    @mute_logger('odoo.sql_db')
    def test_duplicate_code_rejected(self):
        """A duplicate specialty code is rejected by the unique constraint."""
        with self.assertRaises(psycopg2.IntegrityError):
            with self.cr.savepoint():
                self.Specialty.create({'name': 'Cardiology 2', 'code': '320'})
                self.env.flush_all()

    def test_copy_name_suffixed(self):
        """copy() appends ' (copy)' to the specialty name."""
        clone = self.specialty.copy()
        self.assertEqual(clone.name, 'Cardiology (copy)')
