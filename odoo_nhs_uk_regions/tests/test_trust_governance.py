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
from odoo.exceptions import ValidationError
from odoo.tests import Form
from odoo.tests.common import tagged

from .common import UkRegionsCommon


@tagged('post_install', '-at_install')
class TestTrustGovernance(UkRegionsCommon):
    """Cover the nhs.trust extension: the _check_governance_link constraint for
    Wales / NI and the health_system onchange that clears the Welsh LHB."""

    # ---- Wales LHB requirement ---------------------------------------
    def test_wales_lhb_trust_requires_lhb(self):
        """A non-national Welsh trust must carry a Local Health Board."""
        with self.assertRaises(ValidationError):
            self.make_wales_trust('WALNO', lhb=None,
                                  trust_type=self.type_welsh_uhb)

    def test_wales_national_trust_exempt_from_lhb(self):
        """A WELSH_NATIONAL trust (e.g. WAST) is valid with no LHB."""
        trust = self.make_wales_trust('WALNAT', lhb=None,
                                      trust_type=self.type_welsh_national)
        self.assertTrue(trust.id)
        self.assertFalse(trust.welsh_lhb_id)

    def test_wales_sha_trust_exempt_from_lhb(self):
        """A WELSH_SHA trust (e.g. Public Health Wales) is valid with no LHB."""
        trust = self.make_wales_trust('WALSHA', lhb=None,
                                      trust_type=self.type_welsh_sha)
        self.assertTrue(trust.id)

    def test_wales_trust_happy_path(self):
        """A Welsh LHB-backed trust saves and links to its LHB."""
        trust = self.make_wales_trust('WALOK', lhb=self.lhb_aneurin)
        self.assertEqual(trust.welsh_lhb_id, self.lhb_aneurin)
        self.assertEqual(trust.health_system, 'nhs_wales')

    def test_wales_trust_region_must_match_system(self):
        """A Welsh trust pointed at the NI region is rejected."""
        with self.assertRaises(ValidationError):
            self.Trust.create({
                'name': 'Cross Region Wales Trust',
                'ods_code': 'WALXR',
                'health_system': 'nhs_wales',
                'trust_type_id': self.type_welsh_uhb.id,
                'region_id': self.region_ni.id,
                'welsh_lhb_id': self.lhb_aneurin.id,
            })

    # ---- Northern Ireland --------------------------------------------
    def test_ni_trust_happy_path(self):
        """An HSC NI trust with only the NI region is valid."""
        trust = self.make_ni_trust('NITOK')
        self.assertEqual(trust.health_system, 'hsc_ni')
        self.assertEqual(trust.region_id, self.region_ni)

    def test_ni_trust_cannot_have_welsh_lhb(self):
        """An NI HSC trust must not carry any intermediate body (Welsh LHB)."""
        with self.assertRaises(ValidationError):
            self.Trust.create({
                'name': 'NI Trust With LHB',
                'ods_code': 'NIBAD',
                'health_system': 'hsc_ni',
                'trust_type_id': self.type_hsc_trust.id,
                'region_id': self.region_ni.id,
                'welsh_lhb_id': self.lhb_aneurin.id,
            })

    # ---- Onchange -----------------------------------------------------
    def test_onchange_clears_lhb_when_leaving_wales(self):
        """Switching health_system away from Wales clears welsh_lhb_id on the form."""
        form = Form(self.Trust)
        form.name = 'Onchange Trust'
        form.ods_code = 'OCWAL'
        form.health_system = 'nhs_wales'
        form.region_id = self.region_wales
        form.trust_type_id = self.type_welsh_uhb
        form.welsh_lhb_id = self.lhb_aneurin
        self.assertEqual(form.welsh_lhb_id, self.lhb_aneurin)

        # Leaving Wales should blank the Welsh-only relation.
        form.health_system = 'nhs_scotland'
        self.assertFalse(form.welsh_lhb_id)
