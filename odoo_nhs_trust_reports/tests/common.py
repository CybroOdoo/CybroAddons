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
"""Shared fixtures for the Reports & Documents test-suite.

Builds one fully-populated England trust (site, board member, active CQC
inspection) and a Scotland trust, so the PDF template and the Excel export
exercise every conditional branch.
"""
from datetime import date

from odoo.tests.common import TransactionCase


class NhsReportsCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ref = cls.env.ref
        cls.region_ney = ref('odoo_nhs_trust_management.region_england_ney')
        cls.icb_ne = ref('odoo_nhs_trust_management.icb_northeast_cumbria')
        cls.type_acute = ref('odoo_nhs_trust_management.type_england_acute')
        cls.region_sco_w = ref('odoo_nhs_trust_management.region_scotland_w')
        cls.hb_ggc = ref('odoo_nhs_trust_management.hb_greater_glasgow_clyde')
        cls.type_sco = ref('odoo_nhs_trust_management.type_scotland_territorial')

        cls.Trust = cls.env['nhs.trust']
        cls.Export = cls.env['nhs.trust.directory.export']

        cls.trust_en = cls.Trust.create({
            'name': 'Reports England Trust',
            'ods_code': 'RREP',
            'health_system': 'nhs_england',
            'trust_type_id': cls.type_acute.id,
            'region_id': cls.region_ney.id,
            'icb_id': cls.icb_ne.id,
            'foundation_trust': True,
            'annual_income': 1_000_000,
            'annual_expenditure': 900_000,
        })
        cls.trust_sco = cls.Trust.create({
            'name': 'Reports Scotland Trust',
            'ods_code': 'S08REP',
            'health_system': 'nhs_scotland',
            'trust_type_id': cls.type_sco.id,
            'region_id': cls.region_sco_w.id,
            'health_board_id': cls.hb_ggc.id,
        })

        # Populate the England trust so all PDF sections render.
        cls.env['nhs.trust.site'].create({
            'name': 'Reports Royal Hospital', 'trust_id': cls.trust_en.id,
            'site_type': 'acute_hospital', 'bed_capacity': 75, 'city': 'Leeds',
        })
        cls.env['res.partner'].create({
            'name': 'Dr Jane Chair', 'is_nhs_board_member': True,
            'nhs_trust_id': cls.trust_en.id, 'nhs_board_role': 'chair',
        })
        cls.env['nhs.trust.cqc.inspection'].create({
            'trust_id': cls.trust_en.id, 'inspection_date': date(2025, 1, 1),
            'overall_rating': 'good', 'state': 'active',
            'cqc_registration_status': 'registered',
        })

        cls._force_state(cls.trust_en, 'active')
        cls._force_state(cls.trust_sco, 'active')

    @classmethod
    def _force_state(cls, trust, state):
        path = {
            'draft': [], 'under_review': ['under_review'],
            'active': ['under_review', 'active'],
        }[state]
        for step in path:
            trust.with_context(approved_state_change=True).write({'state': step})
