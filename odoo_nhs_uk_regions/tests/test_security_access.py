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
from odoo.exceptions import AccessError
from odoo.tests.common import tagged
from odoo.tools import mute_logger

from .common import UkRegionsCommon


@tagged('post_install', '-at_install')
class TestSecurityAccess(UkRegionsCommon):
    """Cover ir.model.access on nhs.welsh.lhb and the record-rule scoping that
    restricts NHS Trust Users to their allowed Welsh LHBs / NI regions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_user = cls.env.ref(
            'odoo_nhs_trust_management.group_nhs_trust_user')
        cls.group_manager = cls.env.ref(
            'odoo_nhs_trust_management.group_nhs_trust_manager')
        cls.group_admin = cls.env.ref(
            'odoo_nhs_trust_management.group_nhs_trust_admin')

        Users = cls.env['res.users'].with_context(no_reset_password=True)
        # NB: Odoo 19 renamed res.users.groups_id -> group_ids.
        cls.user_user = Users.create({
            'name': 'NHS Region User',
            'login': 'uk_regions_user',
            'group_ids': [(6, 0, [cls.group_user.id])],
        })
        cls.user_manager = Users.create({
            'name': 'NHS Region Manager',
            'login': 'uk_regions_manager',
            'group_ids': [(6, 0, [cls.group_manager.id])],
        })
        cls.user_admin = Users.create({
            'name': 'NHS Region Admin',
            'login': 'uk_regions_admin',
            'group_ids': [(6, 0, [cls.group_admin.id])],
        })

    # ---- ir.model.access on nhs.welsh.lhb ----------------------------
    @mute_logger('odoo.addons.base.models.ir_model')
    def test_user_cannot_create_lhb(self):
        """A plain NHS Trust User has read-only access to Welsh LHBs."""
        with self.assertRaises(AccessError):
            self.Lhb.with_user(self.user_user).create({
                'name': 'User Created LHB',
                'code': '7A9',
                'region_id': self.region_wales.id,
            })

    def test_manager_can_create_lhb(self):
        """An NHS Trust Manager may create Welsh LHBs."""
        lhb = self.Lhb.with_user(self.user_manager).create({
            'name': 'Manager Created LHB',
            'code': '7A9',
            'region_id': self.region_wales.id,
        })
        self.assertTrue(lhb.id)

    @mute_logger('odoo.addons.base.models.ir_model')
    def test_manager_cannot_unlink_lhb(self):
        """A Manager cannot delete Welsh LHBs (perm_unlink reserved to Admin)."""
        lhb = self.make_welsh_lhb('7A9', 'Manager Unlink LHB')
        with self.assertRaises(AccessError):
            lhb.with_user(self.user_manager).unlink()

    def test_admin_can_unlink_lhb(self):
        """An NHS Trust Admin may delete Welsh LHBs."""
        lhb = self.make_welsh_lhb('7A9', 'Admin Unlink LHB')
        lhb.with_user(self.user_admin).unlink()
        self.assertFalse(lhb.exists())

    # ---- record-rule scoping -----------------------------------------
    def test_welsh_lhb_record_rule_scoping(self):
        """A user only sees Welsh trusts whose LHB is in their allowed set."""
        self.user_user.nhs_allowed_welsh_lhb_ids = [(6, 0, [self.lhb_aneurin.id])]
        allowed = self.make_wales_trust('SCAL1', lhb=self.lhb_aneurin)
        denied = self.make_wales_trust('SCAL2', lhb=self.lhb_powys)

        visible = self.Trust.with_user(self.user_user).search(
            [('id', 'in', (allowed + denied).ids)])
        self.assertIn(allowed, visible)
        self.assertNotIn(denied, visible)

    def test_ni_region_record_rule_scoping(self):
        """Granting a user the NI region exposes NI trusts but not foreign Welsh ones."""
        self.user_user.nhs_allowed_region_ids = [(6, 0, [self.region_ni.id])]
        ni_trust = self.make_ni_trust('SCNI1')
        wales_trust = self.make_wales_trust('SCNI2', lhb=self.lhb_powys)

        visible = self.Trust.with_user(self.user_user).search(
            [('id', 'in', (ni_trust + wales_trust).ids)])
        self.assertIn(ni_trust, visible)
        self.assertNotIn(wales_trust, visible)
