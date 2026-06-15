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
from datetime import date, timedelta

from freezegun import freeze_time
from odoo.exceptions import ValidationError, UserError
from odoo.tests import tagged

from .common import NhsTrustCommon


@tagged('post_install', '-at_install')
class TestBoardMember(NhsTrustCommon):
    """res.partner NHS board-member extension: term compute, manager-only
    gating and the trust-state assignment constraint."""

    @freeze_time('2026-06-15')
    def test_is_term_active_compute(self):
        """is_term_active is True only when today falls inside the term."""
        today = date(2026, 6, 15)
        partner = self.env['res.partner'].create({
            'name': 'Active Term',
            'is_nhs_board_member': True,
            'nhs_trust_id': self.trust_en.id,
            'nhs_board_role': 'ceo',
            'term_start_date': today - timedelta(days=10),
            'term_end_date': today + timedelta(days=10),
        })
        self.assertTrue(partner.is_term_active)

        expired = self.env['res.partner'].create({
            'name': 'Expired Term',
            'is_nhs_board_member': True,
            'nhs_trust_id': self.trust_en.id,
            'nhs_board_role': 'non_exec',
            'term_start_date': today - timedelta(days=30),
            'term_end_date': today - timedelta(days=1),
        })
        self.assertFalse(expired.is_term_active)

    def test_non_member_term_inactive(self):
        """A non board-member always reports is_term_active=False."""
        partner = self.env['res.partner'].create({'name': 'Plain Contact'})
        self.assertFalse(partner.is_term_active)

    def test_cannot_assign_to_dissolved_trust(self):
        """_check_trust_state_for_board_member blocks dissolved/suspended trusts."""
        self._force_state(self.trust_en, 'dissolved')
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                'name': 'Late Joiner',
                'is_nhs_board_member': True,
                'nhs_trust_id': self.trust_en.id,
                'nhs_board_role': 'exec',
            })

    def test_non_manager_cannot_create_board_member(self):
        """A plain NHS user cannot create a board-member partner."""
        user = self.env['res.users'].create({
            'name': 'Plain User', 'login': 'nhs_plain_user',
            'group_ids': [(6, 0, [self.env.ref(
                'odoo_nhs_trust_management.group_nhs_trust_user').id])],
        })
        with self.assertRaises(UserError):
            self.env['res.partner'].with_user(user).create({
                'name': 'Illegal Member',
                'is_nhs_board_member': True,
                'nhs_trust_id': self.trust_en.id,
            })

    def test_manager_can_create_board_member(self):
        """An NHS manager may create a board-member partner."""
        manager = self.env['res.users'].create({
            'name': 'NHS Manager', 'login': 'nhs_manager_bm',
            'group_ids': [(6, 0, [self.env.ref(
                'odoo_nhs_trust_management.group_nhs_trust_manager').id])],
        })
        partner = self.env['res.partner'].with_user(manager).create({
            'name': 'Legit Member',
            'is_nhs_board_member': True,
            'nhs_trust_id': self.trust_en.id,
            'nhs_board_role': 'chair',
        })
        self.assertTrue(partner.is_nhs_board_member)
