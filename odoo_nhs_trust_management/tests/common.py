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
"""Shared fixtures for the NHS Trust Management test-suite.

All ORM/business-logic tests inherit from :class:`NhsTrustCommon`, which loads
the master data shipped in ``data/*.xml`` via external IDs and builds a small
set of representative Trusts and scoped users in ``setUpClass`` (so they are
created once and rolled back at the end of the class, not per method).
"""
from odoo.tests.common import TransactionCase


class NhsTrustCommon(TransactionCase):
    """Base fixture: master data refs, helper builders and scoped users."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ref = cls.env.ref

        # ---- Seed master data (loaded by data/*.xml at install) ----------
        # England
        cls.region_ney = ref('odoo_nhs_trust_management.region_england_ney')
        cls.region_ldn = ref('odoo_nhs_trust_management.region_england_ldn')
        cls.icb_ne_cumbria = ref('odoo_nhs_trust_management.icb_northeast_cumbria')
        cls.icb_sy = ref('odoo_nhs_trust_management.icb_south_yorkshire')
        cls.type_acute = ref('odoo_nhs_trust_management.type_england_acute')
        # Scotland
        cls.region_sco_w = ref('odoo_nhs_trust_management.region_scotland_w')
        cls.hb_ggc = ref('odoo_nhs_trust_management.hb_greater_glasgow_clyde')
        cls.type_sco_terr = ref('odoo_nhs_trust_management.type_scotland_territorial')

        cls.NhsTrust = cls.env['nhs.trust']

        # ---- Representative Trusts ---------------------------------------
        cls.trust_en = cls.NhsTrust.create({
            'name': 'Newcastle Hospitals NHS Trust',
            'ods_code': 'rgt',          # lower-case on purpose: create() must upper-case
            'health_system': 'nhs_england',
            'trust_type_id': cls.type_acute.id,
            'region_id': cls.region_ney.id,
            'icb_id': cls.icb_ne_cumbria.id,
        })
        cls.trust_sco = cls.NhsTrust.create({
            'name': 'NHS Greater Glasgow and Clyde Trust',
            'ods_code': 'S08000021X',
            'health_system': 'nhs_scotland',
            'trust_type_id': cls.type_sco_terr.id,
            'region_id': cls.region_sco_w.id,
            'health_board_id': cls.hb_ggc.id,
        })

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #
    @classmethod
    def _make_england_trust(cls, **overrides):
        vals = {
            'name': 'Test England Trust',
            'ods_code': 'RX9',
            'health_system': 'nhs_england',
            'trust_type_id': cls.type_acute.id,
            'region_id': cls.region_ney.id,
            'icb_id': cls.icb_ne_cumbria.id,
        }
        vals.update(overrides)
        return cls.NhsTrust.create(vals)

    @classmethod
    def _force_state(cls, trust, state):
        """Move a trust to ``state`` honouring the legal transition graph,
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
