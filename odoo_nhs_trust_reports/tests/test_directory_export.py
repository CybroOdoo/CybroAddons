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
import base64

from odoo.tests import Form, tagged

from .common import NhsReportsCommon


@tagged('post_install', '-at_install')
class TestDirectoryExport(NhsReportsCommon):
    """nhs.trust.directory.export: domain building, onchange and file output."""

    def test_build_domain_defaults(self):
        """Default (all systems / active) yields just the active-state clause."""
        wiz = self.Export.create({'health_system': 'all', 'status_filter': 'active'})
        self.assertEqual(wiz._build_domain(), [('state', '=', 'active')])

    def test_build_domain_all_filters(self):
        """Each filter contributes its expected leaf to the domain."""
        wiz = self.Export.create({
            'health_system': 'nhs_england',
            'status_filter': 'exclude_dissolved',
            'region_ids': [(6, 0, [self.region_ney.id])],
        })
        domain = wiz._build_domain()
        self.assertIn(('health_system', '=', 'nhs_england'), domain)
        self.assertIn(('state', '!=', 'dissolved'), domain)
        self.assertIn(('region_id', 'in', [self.region_ney.id]), domain)

    def test_build_domain_all_statuses_no_clause(self):
        """status_filter='all' adds no state clause."""
        wiz = self.Export.create({'health_system': 'all', 'status_filter': 'all'})
        self.assertEqual(wiz._build_domain(), [])

    def test_onchange_health_system_clears_regions(self):
        """Changing health_system resets the region filter (onchange)."""
        form = Form(self.Export)
        form.health_system = 'nhs_england'
        form.region_ids.add(self.region_ney)
        form.health_system = 'nhs_scotland'
        self.assertFalse(form.region_ids)

    def test_action_export_generates_xlsx(self):
        """action_export builds a real .xlsx and stores it as base64 on the wizard."""
        wiz = self.Export.create({'health_system': 'all', 'status_filter': 'all'})
        result = wiz.action_export()
        self.assertEqual(result.get('res_model'), 'nhs.trust.directory.export')
        self.assertTrue(wiz.export_file, "export_file must be populated.")
        self.assertTrue(wiz.export_filename.endswith('.xlsx'))
        # XLSX is a ZIP container -> decoded bytes start with the PK signature.
        self.assertEqual(base64.b64decode(wiz.export_file)[:2], b'PK')

    def test_export_respects_status_filter(self):
        """An 'active only' export includes active trusts (sanity on the search)."""
        wiz = self.Export.create({'health_system': 'all', 'status_filter': 'active'})
        trusts = self.env['nhs.trust'].search(wiz._build_domain())
        self.assertIn(self.trust_en, trusts)
        self.assertTrue(all(t.state == 'active' for t in trusts))
