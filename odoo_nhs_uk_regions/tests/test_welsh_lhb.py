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

from odoo.exceptions import ValidationError
from odoo.tests.common import tagged
from odoo.tools import mute_logger

from .common import UkRegionsCommon


@tagged('post_install', '-at_install')
class TestWelshLhb(UkRegionsCommon):
    """Cover the nhs.welsh.lhb model: code normalisation, format & uniqueness
    constraints, the trust_count compute, and the action_view_trusts action."""

    def test_code_uppercased_on_create(self):
        """create() uppercases the ODS code so '7a9' is stored as '7A9'."""
        lhb = self.make_welsh_lhb('7a9', 'Lowercase Create LHB')
        self.assertEqual(lhb.code, '7A9')

    def test_code_uppercased_on_write(self):
        """write() uppercases the ODS code on update."""
        lhb = self.make_welsh_lhb('7A9', 'Write Upper LHB')
        lhb.write({'code': '7a8'})
        self.assertEqual(lhb.code, '7A8')

    def test_code_format_rejects_wrong_length(self):
        """_check_code_format rejects a code that is not exactly 3 chars.

        NB: the field is Char(size=3) so an over-length code is silently
        truncated by the ORM; only a too-short code can reach the length check.
        """
        with self.assertRaises(ValidationError):
            self.make_welsh_lhb('7A', 'Too Short Code LHB')

    def test_code_format_rejects_wrong_prefix(self):
        """_check_code_format rejects a 3-char code not starting with '7A'."""
        with self.assertRaises(ValidationError):
            self.make_welsh_lhb('ABC', 'Bad Prefix LHB')

    @mute_logger('odoo.sql_db')
    def test_code_must_be_unique(self):
        """The unique(code) SQL Constraint blocks a duplicate ODS code at flush."""
        with self.assertRaises(psycopg2.IntegrityError):
            with self.cr.savepoint():
                # 7A6 already belongs to the seeded Aneurin Bevan LHB.
                self.make_welsh_lhb('7A6', 'Duplicate Code LHB')
                self.env.flush_all()

    @mute_logger('odoo.sql_db')
    def test_name_must_be_unique(self):
        """The unique(name) SQL Constraint blocks a duplicate LHB name at flush."""
        with self.assertRaises(psycopg2.IntegrityError):
            with self.cr.savepoint():
                self.make_welsh_lhb('7A9', 'Aneurin Bevan University Health Board')
                self.env.flush_all()

    def test_trust_count_compute(self):
        """trust_count reflects the number of trusts pointing at the LHB."""
        lhb = self.make_welsh_lhb('7A9', 'Counting LHB')
        self.assertEqual(lhb.trust_count, 0)
        self.make_wales_trust('WALC1', lhb=lhb)
        self.make_wales_trust('WALC2', lhb=lhb)
        lhb.invalidate_recordset(['trust_count'])
        self.assertEqual(lhb.trust_count, 2)

    def test_action_view_trusts(self):
        """action_view_trusts returns a window action scoped to this LHB."""
        action = self.lhb_aneurin.action_view_trusts()
        self.assertEqual(action['res_model'], 'nhs.trust')
        self.assertIn(('welsh_lhb_id', '=', self.lhb_aneurin.id), action['domain'])
        self.assertEqual(
            action['context']['default_welsh_lhb_id'], self.lhb_aneurin.id)
        self.assertEqual(action['context']['default_health_system'], 'nhs_wales')
