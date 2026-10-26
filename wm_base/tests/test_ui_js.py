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
from markupsafe import Markup

from odoo.tests import HttpCase, new_test_user, tagged

DASHBOARD_URL = '/odoo/action-wm_base.action_wm_dashboard'


@tagged('post_install', '-at_install', 'wm_base')
class TestUiJs(HttpCase):
    """Browser tours for the wm_base backend JS: navbar, Sign Now, graph and
    chatter patches, and the dashboard drill-downs."""

    def setUp(self):
        super().setUp()
        new_test_user(self.env, login='wm_js_admin', groups='base.group_user,wm_base.group_wm_admin')

    def _need(self, model):
        if model not in self.env:
            self.skipTest("%s is not installed" % model)

    # -- navbar -------------------------------------------------------------
    def test_navbar_sidebar_tour(self):
        self.browser_size = '1366x768'
        self.start_tour(DASHBOARD_URL, 'wm_navbar_tour', login='wm_js_admin')

    def test_navbar_mobile_drawer_tour(self):
        self.browser_size = '600x800'
        self.start_tour(DASHBOARD_URL, 'wm_navbar_mobile_tour', login='wm_js_admin')

    # -- sign now -----------------------------------------------------------
    def test_sign_now_tour(self):
        self.start_tour('/odoo/action-wm_base.action_wm_signature_sign_now', 'wm_sign_now_tour',
                        login='wm_js_admin')

    # -- graph renderer patch ----------------------------------------------
    def test_graph_renderer_patch_tour(self):
        view = self.env['ir.ui.view'].create({
            'name': 'wm.js.test.partner.graph',
            'model': 'res.partner',
            'type': 'graph',
            'arch': '<graph type="bar"><field name="company_id"/></graph>',
        })
        action = self.env['ir.actions.act_window'].create({
            'name': 'WM Graph Patch Test',
            'res_model': 'res.partner',
            'view_mode': 'graph',
            'view_ids': [(0, 0, {'view_mode': 'graph', 'view_id': view.id})],
        })
        self.start_tour('/odoo/action-%s' % action.id, 'wm_graph_renderer_tour', login='wm_js_admin')

    # -- chatter shadow patch ----------------------------------------------
    def test_chatter_shadow_patch_tour(self):
        partner = self.env['res.partner'].create({'name': 'Shadow Patch Partner'})
        partner.message_post(
            body=Markup('<p>Shadow patch body</p>'), message_type='email', subtype_xmlid='mail.mt_note')
        self.start_tour('/odoo/res.partner/%s' % partner.id, 'wm_chatter_shadow_tour',
                        login='wm_js_admin')

    # -- dashboard drill-downs ---------------------------------------------
    def test_dashboard_inspection_drilldowns(self):
        self._need('wm.batch.inspection')
        for tour in ('wm_dashboard_inspection_tour', 'wm_dashboard_inspection_all_tour',
                     'wm_dashboard_legend_inspection_tour'):
            with self.subTest(tour=tour):
                self.start_tour(DASHBOARD_URL, tour, login='wm_js_admin')

    def test_dashboard_collection_drilldowns(self):
        self._need('wm.collection.order')
        for tour in ('wm_dashboard_orders_all_tour', 'wm_dashboard_efficiency_tour',
                     'wm_dashboard_awaiting_signature_tour'):
            with self.subTest(tour=tour):
                self.start_tour(DASHBOARD_URL, tour, login='wm_js_admin')

    def test_dashboard_fleet_drilldown(self):
        self._need('fleet.vehicle')
        self.start_tour(DASHBOARD_URL, 'wm_dashboard_fleet_tour', login='wm_js_admin')
