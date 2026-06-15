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
"""Shared fixtures for the Operations & Compliance test-suite.

Builds an England and a Scotland trust (reusing the Foundation module's seed
master data), plus a site, department and specialty, once per class.
"""
from odoo.tests.common import TransactionCase


class NhsOpsCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ref = cls.env.ref
        # Foundation-module seed master data
        cls.region_ney = ref('odoo_nhs_trust_management.region_england_ney')
        cls.icb_ne = ref('odoo_nhs_trust_management.icb_northeast_cumbria')
        cls.type_acute = ref('odoo_nhs_trust_management.type_england_acute')
        cls.region_sco_w = ref('odoo_nhs_trust_management.region_scotland_w')
        cls.hb_ggc = ref('odoo_nhs_trust_management.hb_greater_glasgow_clyde')
        cls.type_sco = ref('odoo_nhs_trust_management.type_scotland_territorial')

        cls.Trust = cls.env['nhs.trust']
        cls.Site = cls.env['nhs.trust.site']
        cls.Dept = cls.env['nhs.trust.department']
        cls.Cqc = cls.env['nhs.trust.cqc.inspection']
        cls.Specialty = cls.env['nhs.trust.specialty']

        cls.trust_en = cls.Trust.create({
            'name': 'Ops England Trust',
            'ods_code': 'ROP1',
            'health_system': 'nhs_england',
            'trust_type_id': cls.type_acute.id,
            'region_id': cls.region_ney.id,
            'icb_id': cls.icb_ne.id,
        })
        cls.trust_sco = cls.Trust.create({
            'name': 'Ops Scotland Trust',
            'ods_code': 'S08OPS',
            'health_system': 'nhs_scotland',
            'trust_type_id': cls.type_sco.id,
            'region_id': cls.region_sco_w.id,
            'health_board_id': cls.hb_ggc.id,
        })

        cls.specialty = cls.Specialty.create({'name': 'Cardiology', 'code': '320'})
        cls.site = cls.Site.create({
            'name': 'Royal London Hospital',
            'trust_id': cls.trust_en.id,
            'site_type': 'acute_hospital',
            'bed_capacity': 100,
        })
        cls.dept = cls.Dept.create({
            'name': 'Emergency Department',
            'site_id': cls.site.id,
            'department_type': 'clinical',
        })

    @classmethod
    def _force_state(cls, trust, state):
        """Move a trust to ``state`` along the legal transition graph,
        bypassing the wizard-only guard via the approved context."""
        path = {
            'draft': [],
            'under_review': ['under_review'],
            'active': ['under_review', 'active'],
            'special_measures': ['under_review', 'active', 'special_measures'],
            'suspended': ['under_review', 'active', 'suspended'],
            'merging': ['under_review', 'active', 'merging'],
            'dissolved': ['under_review', 'active', 'dissolved'],
        }[state]
        for step in path:
            trust.with_context(approved_state_change=True).write({'state': step})
