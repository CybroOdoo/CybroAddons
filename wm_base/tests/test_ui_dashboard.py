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
from datetime import timedelta

from odoo import fields
from odoo.tests import HttpCase, new_test_user, tagged


@tagged('post_install', '-at_install', 'wm_base')
class TestUiDashboard(HttpCase):
    """Browser tours for the operations dashboard and its drill-downs."""

    def setUp(self):
        super().setUp()
        new_test_user(self.env, login='wm_dash_admin', groups='base.group_user,wm_base.group_wm_admin')

    def test_dashboard_tour(self):
        # The drill-down of the first tour opens collection orders: without the
        # collection module only the dashboard itself can be checked.
        tour = 'wm_dashboard_tour' if 'wm.collection.order' in self.env else 'wm_dashboard_basic_tour'
        self.start_tour('/odoo/action-wm_base.action_wm_dashboard', tour, login='wm_dash_admin')

    def test_dashboard_revenue_drilldown_tour(self):
        if 'wm.collection.order' not in self.env:
            self.skipTest("Collection module not installed")
        # Unbilled order revenue today, so the "Orders" revenue item is shown
        now = fields.Datetime.now()
        partner = self.env['res.partner'].create({'name': 'Dashboard Tour Customer'})
        category = self.env['wm.waste.category'].create({'name': 'Dashboard Tour Waste', 'code': 'DSHTR'})
        self.env['wm.collection.order'].create({
            'partner_id': partner.id,
            'collection_point_id': self.env['wm.collection.point'].create({
                'name': 'Dashboard Tour Point', 'partner_id': partner.id}).id,
            'scheduled_start': now,
            'scheduled_end': now + timedelta(hours=1),
            'state': 'completed',
            'order_line_ids': [(0, 0, {'category_id': category.id, 'weight': 10.0, 'price': 5.0})],
        })
        self.start_tour('/odoo/action-wm_base.action_wm_dashboard', 'wm_dashboard_revenue_tour', login='wm_dash_admin')
