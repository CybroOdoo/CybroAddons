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
from odoo.tests.common import TransactionCase


class UkRegionsCommon(TransactionCase):
    """Shared fixtures for the UK Regions extension test suite.

    Seeds references to the module's own ``noupdate`` data (regions, trust
    types, LHBs) and provides helpers to build Welsh / NI trusts that satisfy
    the inherited governance constraints.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ref = cls.env.ref

        # Regions seeded by data/nhs_region_data.xml
        cls.region_wales = ref('odoo_nhs_uk_regions.region_wales')
        cls.region_ni = ref('odoo_nhs_uk_regions.region_ni')

        # Trust types seeded by data/nhs_trust_type_data.xml
        cls.type_welsh_uhb = ref('odoo_nhs_uk_regions.trust_type_welsh_uhb')
        cls.type_welsh_thb = ref('odoo_nhs_uk_regions.trust_type_welsh_thb')
        cls.type_welsh_national = ref('odoo_nhs_uk_regions.trust_type_welsh_national')
        cls.type_welsh_sha = ref('odoo_nhs_uk_regions.trust_type_welsh_sha')
        cls.type_hsc_trust = ref('odoo_nhs_uk_regions.trust_type_hsc_trust')

        # LHBs seeded by data/nhs_welsh_lhb_data.xml
        cls.lhb_aneurin = ref('odoo_nhs_uk_regions.lhb_aneurin_bevan')   # 7A6
        cls.lhb_powys = ref('odoo_nhs_uk_regions.lhb_powys')             # 7A3 (teaching)

        cls.Trust = cls.env['nhs.trust']
        cls.Lhb = cls.env['nhs.welsh.lhb']

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def make_welsh_lhb(self, code, name, lhb_type='university'):
        """Create a Welsh LHB attached to the Wales region."""
        return self.Lhb.create({
            'name': name,
            'code': code,
            'region_id': self.region_wales.id,
            'lhb_type': lhb_type,
        })

    def make_wales_trust(self, code, lhb=None, trust_type=None, name=None):
        """Create an NHS Wales trust that passes the governance constraint.

        Pass ``lhb=None`` together with a national/SHA ``trust_type`` to build a
        national Welsh trust (which is exempt from the LHB requirement).
        """
        return self.Trust.create({
            'name': name or ('Wales Trust %s' % code),
            'ods_code': code,
            'health_system': 'nhs_wales',
            'trust_type_id': (trust_type or self.type_welsh_uhb).id,
            'region_id': self.region_wales.id,
            'welsh_lhb_id': lhb.id if lhb else False,
        })

    def make_ni_trust(self, code, name=None):
        """Create an HSC Northern Ireland trust (attaches directly to NI region)."""
        return self.Trust.create({
            'name': name or ('NI Trust %s' % code),
            'ods_code': code,
            'health_system': 'hsc_ni',
            'trust_type_id': self.type_hsc_trust.id,
            'region_id': self.region_ni.id,
        })
