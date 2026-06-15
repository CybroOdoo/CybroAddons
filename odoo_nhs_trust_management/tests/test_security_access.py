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
from odoo.tests import tagged, users

from .common import NhsTrustCommon


@tagged('post_install', '-at_install')
class TestSecurityAccess(NhsTrustCommon):
    """Access-rights matrix and geographic record-rule scoping."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        group_user = cls.env.ref('odoo_nhs_trust_management.group_nhs_trust_user')
        group_mgr = cls.env.ref('odoo_nhs_trust_management.group_nhs_trust_manager')

        # A trust the scoped user is NOT allowed to see (different ICB).
        cls.trust_sy = cls._make_england_trust(
            name='South Yorkshire Trust', ods_code='RSY1',
            icb_id=cls.icb_sy.id)

        # Scoped user: only NE & North Cumbria ICB.
        cls.scoped_user = cls.env['res.users'].create({
            'name': 'Scoped England User',
            'login': 'nhs_scoped_user',
            'group_ids': [(6, 0, [group_user.id])],
            'nhs_allowed_icb_ids': [(6, 0, [cls.icb_ne_cumbria.id])],
        })
        cls.manager_user = cls.env['res.users'].create({
            'name': 'Global Manager',
            'login': 'nhs_global_mgr',
            'group_ids': [(6, 0, [group_mgr.id])],
        })

    # ------------------------------------------------------------------ #
    #  ACL (model-level)
    # ------------------------------------------------------------------ #
    @users('nhs_scoped_user')
    def test_user_is_read_only_on_trust(self):
        """A plain NHS user has no write permission on nhs.trust."""
        trust = self.env['nhs.trust'].browse(self.trust_en.id)
        with self.assertRaises(AccessError):
            trust.write({'short_name': 'Hacked'})

    # ------------------------------------------------------------------ #
    #  Record rules (geographic scoping)
    # ------------------------------------------------------------------ #
    def test_user_sees_only_allowed_icb(self):
        """The scoped user sees trusts in allowed ICBs only."""
        visible = self.env['nhs.trust'].with_user(self.scoped_user).search([])
        self.assertIn(self.trust_en, visible)          # NE & N Cumbria
        self.assertNotIn(self.trust_sy, visible)        # South Yorkshire
        self.assertNotIn(self.trust_sco, visible)       # Scotland

    def test_manager_sees_all_trusts(self):
        """A manager has the global [(1,'=',1)] rule and sees every trust."""
        visible = self.env['nhs.trust'].with_user(self.manager_user).search([])
        self.assertIn(self.trust_en, visible)
        self.assertIn(self.trust_sy, visible)
        self.assertIn(self.trust_sco, visible)

    def test_state_log_scoped_to_user_trusts(self):
        """State-log visibility follows the same geographic scope as trusts."""
        self.env['nhs.trust.state.log'].create({
            'trust_id': self.trust_sy.id, 'to_state': 'under_review',
            'reason': 'seed sy',
        })
        self.env['nhs.trust.state.log'].create({
            'trust_id': self.trust_en.id, 'to_state': 'under_review',
            'reason': 'seed en',
        })
        logs = self.env['nhs.trust.state.log'].with_user(self.scoped_user).search([])
        self.assertTrue(all(l.trust_id == self.trust_en for l in logs),
                        "Scoped user must only see logs of in-scope trusts.")

    # ------------------------------------------------------------------ #
    #  Performance guard (ties Part 4 N+1 review to an executable check)
    # ------------------------------------------------------------------ #
    def test_region_trust_count_is_not_n_plus_1(self):
        """region.trust_count must issue the SAME number of queries regardless
        of how many regions are read (it uses a single grouped query). This is
        a robust N+1 guard that does not hard-code an absolute query count."""
        Region = self.env['nhs.region']

        one = Region.search([('health_system', '=', 'nhs_england')], limit=1)
        one.invalidate_recordset(['trust_count'])
        with self.assertQueryCount(default=1):
            one.mapped('trust_count')

        many = Region.search([('health_system', '=', 'nhs_england')])
        self.assertGreater(len(many), 1, "Need several England regions seeded.")
        many.invalidate_recordset(['trust_count'])
        with self.assertQueryCount(default=1):
            # still ONE grouped query for all regions -> no N+1
            many.mapped('trust_count')
