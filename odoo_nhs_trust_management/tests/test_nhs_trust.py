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
from odoo.exceptions import ValidationError, UserError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import NhsTrustCommon


@tagged('post_install', '-at_install')
class TestNhsTrust(NhsTrustCommon):
    """Core nhs.trust model: CRUD overrides, constraints, computes, copy."""

    # ------------------------------------------------------------------ #
    #  Happy path + create() normalisation
    # ------------------------------------------------------------------ #
    def test_create_uppercases_ods_code(self):
        """create() force-upper-cases ods_code (fixture passed 'rgt')."""
        self.assertEqual(self.trust_en.ods_code, 'RGT')
        self.assertEqual(self.trust_en.state, 'draft',
                         "A new Trust must default to the 'draft' workflow state.")

    def test_write_uppercases_ods_code(self):
        """write() force-upper-cases ods_code."""
        self.trust_en.write({'ods_code': 'rx9'})
        self.assertEqual(self.trust_en.ods_code, 'RX9')

    # ------------------------------------------------------------------ #
    #  SQL + python constraints
    # ------------------------------------------------------------------ #
    @mute_logger('odoo.sql_db')
    def test_ods_code_unique_sql_constraint(self):
        """The ods_code UNIQUE SQL constraint rejects duplicates."""
        with self.assertRaises(psycopg2.IntegrityError):
            with self.cr.savepoint():
                self._make_england_trust(name='Dup', ods_code='RGT')
                self.env.flush_all()  # force the INSERT so the UNIQUE fires

    def test_ods_code_must_be_alphanumeric(self):
        """_check_ods_code rejects non-alphanumeric codes."""
        with self.assertRaises(ValidationError):
            self._make_england_trust(ods_code='RG-1')

    def test_england_ods_code_length(self):
        """England ODS codes must be 3..5 chars."""
        with self.assertRaises(ValidationError):
            self._make_england_trust(ods_code='RG')          # too short
        with self.assertRaises(ValidationError):
            self._make_england_trust(ods_code='RGT123')      # too long

    def test_scotland_ods_code_rules(self):
        """Scotland ODS codes must start with 'S' and be 3..10 chars."""
        with self.assertRaises(ValidationError):
            self.NhsTrust.create({
                'name': 'Bad Scot', 'ods_code': 'X08',
                'health_system': 'nhs_scotland',
                'trust_type_id': self.type_sco_terr.id,
                'region_id': self.region_sco_w.id,
                'health_board_id': self.hb_ggc.id,
            })

    def test_geographic_consistency_england(self):
        """England trust must have an ICB, and that ICB must sit in its region."""
        # ICB from the wrong region (South Yorkshire ICB but NEY region is fine;
        # use London region with a NEY ICB to force the mismatch).
        with self.assertRaises(ValidationError):
            self._make_england_trust(region_id=self.region_ldn.id)

    def test_england_cannot_have_health_board(self):
        """An England trust may not reference a Scottish Health Board."""
        with self.assertRaises(ValidationError):
            self._make_england_trust(health_board_id=self.hb_ggc.id)

    def test_scotland_requires_health_board(self):
        """A Scotland trust without a Health Board is rejected."""
        with self.assertRaises(ValidationError):
            self.NhsTrust.create({
                'name': 'No HB', 'ods_code': 'S08001',
                'health_system': 'nhs_scotland',
                'trust_type_id': self.type_sco_terr.id,
                'region_id': self.region_sco_w.id,
            })

    def test_scotland_cannot_be_special_measures(self):
        """_check_state_health_system blocks Special Measures for Scotland."""
        self._force_state(self.trust_sco, 'active')
        with self.assertRaises(ValidationError):
            self.trust_sco.with_context(approved_state_change=True).write(
                {'state': 'special_measures'})

    # ------------------------------------------------------------------ #
    #  Computed fields
    # ------------------------------------------------------------------ #
    def test_board_member_count_compute(self):
        """board_member_count reflects the linked board members."""
        self.assertEqual(self.trust_en.board_member_count, 0)
        self.env['res.partner'].create({
            'name': 'Jane Chair',
            'is_nhs_board_member': True,
            'nhs_trust_id': self.trust_en.id,
            'nhs_board_role': 'chair',
        })
        self.assertEqual(self.trust_en.board_member_count, 1)

    # ------------------------------------------------------------------ #
    #  copy()
    # ------------------------------------------------------------------ #
    def test_copy_generates_unique_ods_and_name(self):
        """Duplicating a Trust yields a unique ODS code, a '(copy)' name and
        resets the workflow state to draft (state has copy=False)."""
        self._force_state(self.trust_en, 'active')
        clone = self.trust_en.copy()
        self.assertNotEqual(clone.ods_code, self.trust_en.ods_code)
        self.assertIn('copy', clone.name.lower())
        self.assertEqual(clone.state, 'draft',
                         "state is copy=False so the clone must start in draft.")

    # ------------------------------------------------------------------ #
    #  unlink()
    # ------------------------------------------------------------------ #
    def test_unlink_only_in_draft(self):
        """Only draft trusts may be deleted."""
        draft = self._make_england_trust(name='Deletable', ods_code='RDEL')
        draft.unlink()  # no raise

        active = self._make_england_trust(name='Locked', ods_code='RLCK')
        self._force_state(active, 'active')
        with self.assertRaises(UserError):
            active.unlink()
