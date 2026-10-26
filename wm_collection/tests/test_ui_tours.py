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
from odoo import fields
from odoo.tests import HttpCase, new_test_user, tagged

XSS_NAME = 'XSS <img src=x onerror="window.__wm_xss=1">'


@tagged('post_install', '-at_install', 'wm_collection')
class TestUiMapTours(HttpCase):
    """Browser tours for the route map widget and the collection point map view."""

    def setUp(self):
        super().setUp()
        self.user = new_test_user(self.env, login='wm_tour_admin',
                                  groups='base.group_user,wm_base.group_wm_admin')
        self.partner = self.env['res.partner'].create({'name': 'Tour Customer ' + XSS_NAME})
        us = self.env.ref('base.us')
        coords = [(40.7128, -74.0060), (40.7306, -73.9352), (40.6782, -73.9442), (40.7580, -73.9855)]
        self.points = self.env['wm.collection.point'].create([{
            'name': (XSS_NAME if i == 0 else 'Tour Point %d' % i),
            'partner_id': self.partner.id,
            'street': '%d Tour St' % i,
            'city': 'New York',
            'country_id': us.id,
            'latitude': lat,
            'longitude': lng,
        } for i, (lat, lng) in enumerate(coords)])
        self.route = self.env['wm.route'].create({
            'date': fields.Date.context_today(self.user),
            'line_ids': [(0, 0, {'collection_point_id': p.id, 'sequence': (i + 1) * 10})
                         for i, p in enumerate(self.points[:3])],
        })

    def test_route_map_tour(self):
        """Route map: escaped popups, single-fire buttons, live redraw after Add to Route."""
        self.start_tour(f'/odoo/wm.route/{self.route.id}', 'wm_route_map_tour', login='wm_tour_admin')
        self.assertEqual(len(self.route.line_ids), 4, "Exactly one stop added")
        added = self.route.line_ids.collection_point_id - self.points[:3]
        orders = self.env['wm.collection.order'].search([
            ('route_id', '=', self.route.id), ('collection_point_id', 'in', added.ids)])
        self.assertEqual(len(orders), 1, "Add to Route fired exactly once")

    def test_collection_point_map_tour(self):
        """Collection point map (wm_map view type) renders escaped popups."""
        self.start_tour('/odoo/action-wm_collection.action_wm_collection_point',
                        'wm_collection_point_map_tour', login='wm_tour_admin')
