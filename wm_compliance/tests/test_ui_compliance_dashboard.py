#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import HttpCase, new_test_user, tagged


@tagged('post_install', '-at_install', 'wm_compliance')
class TestUiComplianceDashboard(HttpCase):
    """Browser tour for the compliance dashboard and its manifest drill-down."""

    def test_compliance_dashboard_tour(self):
        new_test_user(self.env, login='wm_cd_admin', groups='base.group_user,wm_base.group_wm_admin')
        self.start_tour('/odoo/action-wm_compliance.action_wm_compliance_dashboard_client',
                        'wm_compliance_dashboard_tour', login='wm_cd_admin')
