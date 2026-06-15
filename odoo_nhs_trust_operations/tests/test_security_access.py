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
from odoo.tests import tagged

from .common import NhsOpsCommon


@tagged('post_install', '-at_install')
class TestOpsSecurity(NhsOpsCommon):
    """ACL + geographic record-rule scoping for sites/departments/CQC."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        icb_sy = cls.env.ref('odoo_nhs_trust_management.icb_south_yorkshire')
        gu = cls.env.ref('odoo_nhs_trust_management.group_nhs_trust_user')
        gm = cls.env.ref('odoo_nhs_trust_management.group_nhs_trust_manager')

        # A trust + site OUTSIDE the scoped user's allowed ICB.
        cls.trust_sy = cls.Trust.create({
            'name': 'SY Trust', 'ods_code': 'RSY9',
            'health_system': 'nhs_england', 'trust_type_id': cls.type_acute.id,
            'region_id': cls.region_ney.id, 'icb_id': icb_sy.id,
        })
        cls.site_sy = cls.Site.create({
            'name': 'SY Hospital', 'trust_id': cls.trust_sy.id,
            'site_type': 'acute_hospital',
        })

        cls.scoped_user = cls.env['res.users'].create({
            'name': 'Scoped Ops User', 'login': 'ops_scoped_user',
            'group_ids': [(6, 0, [gu.id])],
            'nhs_allowed_icb_ids': [(6, 0, [cls.icb_ne.id])],
        })
        cls.manager_user = cls.env['res.users'].create({
            'name': 'Ops Manager', 'login': 'ops_manager',
            'group_ids': [(6, 0, [gm.id])],
        })

    def test_user_sees_only_allowed_icb_sites(self):
        """Scoped user sees sites only for trusts in their allowed ICBs."""
        visible = self.Site.with_user(self.scoped_user).search([])
        self.assertIn(self.site, visible)          # trust_en -> icb_ne (allowed)
        self.assertNotIn(self.site_sy, visible)     # trust_sy -> icb_sy (not allowed)

    def test_user_sees_only_allowed_icb_departments(self):
        """Department scoping follows trust_id.icb_id too."""
        visible = self.Dept.with_user(self.scoped_user).search([])
        self.assertIn(self.dept, visible)
        self.assertTrue(all(d.trust_id == self.trust_en for d in visible))

    def test_user_cannot_create_site(self):
        """Plain NHS user is read-only on sites (ACL perm_create=0)."""
        with self.assertRaises(AccessError):
            self.Site.with_user(self.scoped_user).create({
                'name': 'Hack Site', 'trust_id': self.trust_en.id,
                'site_type': 'clinic',
            })

    def test_manager_global_access(self):
        """Manager has the global rule and sees every site, and may create."""
        visible = self.Site.with_user(self.manager_user).search([])
        self.assertIn(self.site, visible)
        self.assertIn(self.site_sy, visible)
        new = self.Site.with_user(self.manager_user).create({
            'name': 'Mgr Site', 'trust_id': self.trust_en.id, 'site_type': 'clinic',
        })
        self.assertTrue(new.exists())
