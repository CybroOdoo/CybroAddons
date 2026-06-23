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


class OdsSyncCommon(TransactionCase):
    """Shared fixtures for the ODS Sync test suite.

    The ACLs (correctly) grant only the ODS Sync Operator group create/write on
    the sync models, so the test user is added to that group. England seed data
    from ``odoo_nhs_trust_management`` is used as the resolution target — the
    Wales/NI paths are skipped here because ``odoo_nhs_uk_regions`` is not a
    dependency of this module.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ref = cls.env.ref

        cls.operator_group = ref('odoo_nhs_ods_sync.group_nhs_ods_sync_operator')
        cls.env.user.group_ids = [(4, cls.operator_group.id)]

        # England seed data (odoo_nhs_trust_management)
        cls.region_england = ref('odoo_nhs_trust_management.region_england_ney')
        cls.type_acute = ref('odoo_nhs_trust_management.type_england_acute')
        cls.type_mental = ref('odoo_nhs_trust_management.type_england_mental')
        cls.icb_gm = ref('odoo_nhs_trust_management.icb_greater_manchester')

        # Role mappings seeded by this module
        cls.role_ro197 = ref('odoo_nhs_ods_sync.role_map_ro197')   # creates_trust=True
        cls.role_ro242 = ref('odoo_nhs_ods_sync.role_map_ro242')   # mental
        cls.role_ro165 = ref('odoo_nhs_ods_sync.role_map_ro165')   # creates_trust=False

        cls.Trust = cls.env['nhs.trust']
        cls.OdsOrg = cls.env['nhs.ods.organisation']
        cls.Run = cls.env['nhs.ods.sync.run']
        cls.Detail = cls.env['nhs.ods.sync.detail']
        cls.Conflict = cls.env['nhs.ods.sync.conflict']
        cls.Provenance = cls.env['nhs.ods.field.provenance']

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def make_england_trust(self, ods_code, state='active', **extra):
        """Create an England trust under sync context (governance bypassed)."""
        vals = {
            'name': extra.pop('name', 'Trust %s' % ods_code),
            'ods_code': ods_code,
            'health_system': 'nhs_england',
            'trust_type_id': self.type_acute.id,
            'region_id': self.region_england.id,
            'state': state,
        }
        vals.update(extra)
        return self.Trust.with_context(nhs_ods_sync=True).create(vals)

    def make_ods_org(self, ods_code, **extra):
        """Create a cached ODS organisation record."""
        vals = {'ods_code': ods_code, 'name': extra.pop('name', 'Org %s' % ods_code),
                'status': 'active'}
        vals.update(extra)
        return self.OdsOrg.create(vals)

    def make_run(self, run_type='targeted', **extra):
        """Create a sync run record (sequence auto-assigns the reference)."""
        vals = {'run_type': run_type}
        vals.update(extra)
        return self.Run.create(vals)

    def parsed_for(self, trust, **overrides):
        """Build a parsed-ODS dict that mirrors a trust, overriding select keys.

        Used to drive the conflict detector / apply logic with a controlled diff.
        """
        data = {
            'ods_code': trust.ods_code,
            'name': trust.name,
            'status': 'active',
            'primary_role_code': 'RO197',
            'address_line1': trust.street or None,
            'address_line2': trust.street2 or None,
            'city': trust.city or None,
            'postcode': trust.zip or None,
            'phone': trust.phone or None,
            'operational_start_date': trust.establishment_date or None,
            'country': '',
            'active_relations': [],
        }
        data.update(overrides)
        return data
