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
from odoo.tests import tagged

from .common import NhsReportsCommon

REPORT = 'odoo_nhs_trust_reports.action_report_nhs_trust_profile'


@tagged('post_install', '-at_install')
class TestProfileReport(NhsReportsCommon):
    """QWeb profile report renders without error and includes key content.

    Rendering HTML (not PDF) avoids the wkhtmltopdf dependency while still
    fully exercising the template's QWeb expressions and branches.
    """

    def _html(self, trust):
        html, content_type = self.env['ir.actions.report']._render_qweb_html(
            REPORT, trust.ids)
        self.assertEqual(content_type, 'html')
        return html.decode() if isinstance(html, bytes) else html

    def test_england_report_renders_all_sections(self):
        """England trust report includes governance, sites and CQC history."""
        html = self._html(self.trust_en)
        self.assertIn('Reports England Trust', html)
        self.assertIn('NHS Foundation Trust', html)        # foundation badge
        self.assertIn('Sites', html)                       # site section
        self.assertIn('Reports Royal Hospital', html)
        self.assertIn('CQC Inspection History', html)      # England-only section
        self.assertIn('Dr Jane Chair', html)               # board member table

    def test_scotland_report_renders_without_cqc(self):
        """Scotland trust renders fine and omits the England-only CQC section."""
        html = self._html(self.trust_sco)
        self.assertIn('Reports Scotland Trust', html)
        self.assertIn('NHS Scotland', html)
        self.assertNotIn('CQC Inspection History', html)

    def test_report_action_bound_to_trust(self):
        """The report action is bound to nhs.trust as a Print menu entry."""
        report = self.env.ref(REPORT)
        self.assertEqual(report.model, 'nhs.trust')
        self.assertEqual(report.report_type, 'qweb-pdf')
        self.assertEqual(report.binding_model_id.model, 'nhs.trust')
