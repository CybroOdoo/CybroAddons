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

from odoo.tests.common import tagged
from odoo.tools import mute_logger

from .common import OdsSyncCommon


@tagged('post_install', '-at_install')
class TestOdsOrganisation(OdsSyncCommon):
    """Cover the nhs.ods.organisation cache model: normalisation on store, the
    unique-code constraint, and the display_name compute."""

    def test_create_normalises_code_and_name(self):
        """create() uppercases ods_code and title-cases an ALL-CAPS name."""
        org = self.OdsOrg.create({'ods_code': 'rw1', 'name': 'BARTS HEALTH NHS TRUST'})
        self.assertEqual(org.ods_code, 'RW1')
        self.assertEqual(org.name, 'Barts Health Nhs Trust')

    def test_write_uppercases_code(self):
        """write() uppercases the ods_code on update."""
        org = self.make_ods_org('RW1')
        org.write({'ods_code': 'rgt'})
        self.assertEqual(org.ods_code, 'RGT')

    def test_mixed_case_name_preserved(self):
        """A non-ALL-CAPS name is stored verbatim (only ALL-CAPS is title-cased)."""
        org = self.OdsOrg.create({'ods_code': 'RGT', 'name': 'Cambridge University Hospitals'})
        self.assertEqual(org.name, 'Cambridge University Hospitals')

    @mute_logger('odoo.sql_db')
    def test_ods_code_unique(self):
        """The unique(ods_code) Constraint blocks a duplicate cache entry at flush."""
        self.make_ods_org('RW1')
        with self.assertRaises(psycopg2.IntegrityError):
            with self.cr.savepoint():
                self.make_ods_org('RW1', name='Duplicate')
                self.env.flush_all()

    def test_display_name_format(self):
        """display_name renders as '[CODE] Name'."""
        org = self.make_ods_org('RW1', name='Barts Health')
        self.assertEqual(org.display_name, '[RW1] Barts Health')
