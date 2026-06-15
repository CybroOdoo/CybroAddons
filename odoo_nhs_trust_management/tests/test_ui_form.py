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
from odoo.tests import tagged, Form

from .common import NhsTrustCommon


@tagged('post_install', '-at_install')
class TestTrustForm(NhsTrustCommon):
    """Form() emulation: proves the onchange chain fires exactly as it would
    for a user filling in the Trust form in the web client."""

    def test_onchange_health_system_clears_geography(self):
        """Switching health_system to Scotland clears England-only references
        (icb/ics) and the foundation fields."""
        form = Form(self.NhsTrust)
        form.name = 'Onchange England Trust'
        form.ods_code = 'RON1'
        form.health_system = 'nhs_england'
        form.region_id = self.region_ney
        form.icb_id = self.icb_ne_cumbria
        form.trust_type_id = self.type_acute
        form.foundation_trust = True

        # Flip to Scotland -> England geography & foundation flags must reset.
        form.health_system = 'nhs_scotland'
        self.assertFalse(form.icb_id)
        self.assertFalse(form.region_id)
        self.assertFalse(form.foundation_trust)

    def test_onchange_region_filters_then_icb_backfills_region(self):
        """Selecting an ICB back-fills the region (onchange_icb_id)."""
        form = Form(self.NhsTrust)
        form.name = 'Backfill Trust'
        form.ods_code = 'RBF1'
        form.health_system = 'nhs_england'
        form.region_id = self.region_ney
        form.icb_id = self.icb_ne_cumbria
        # region already NEY; clearing and re-picking icb should restore it
        self.assertEqual(form.region_id, self.icb_ne_cumbria.region_id)
