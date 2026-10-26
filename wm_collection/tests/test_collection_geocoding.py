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
from unittest.mock import patch

import requests

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'wm_collection')
class TestCollectionGeocoding(TransactionCase):
    """Geocoding runs in the background: saving a point never calls the geocoding service."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Point = cls.env['wm.collection.point']
        cls.PointClass = type(cls.Point)
        cls.CronClass = type(cls.env['ir.cron'])
        cls.cron = cls.env.ref('wm_collection.ir_cron_geocode_collection_points')
        cls.country = cls.env.ref('base.us')

    def _run_cron(self):
        # _commit_progress commits outside a real cron run: not allowed in tests
        with patch.object(self.CronClass, '_commit_progress', return_value=60.0):
            self.Point._cron_geocode_pending()

    def test_save_queues_without_network_call(self):
        """Creating or moving a point flags it and wakes the cron; no HTTP request is made."""
        with patch('requests.get', side_effect=AssertionError("geocoding must not run on save")):
            point = self.Point.create({'name': 'Geo Async', 'street': '1 Main St', 'country_id': self.country.id})
            self.assertTrue(point.geo_pending)
            self.assertTrue(self.env['ir.cron.trigger'].search_count([('cron_id', '=', self.cron.id)]))

            point.geo_pending = False
            point.write({'latitude': 10.0, 'longitude': 20.0})
            point.write({'street': '2 Other St'})
            self.assertTrue(point.geo_pending)
            self.assertFalse(point.latitude)

    def test_explicit_coordinates_clear_pending(self):
        """Coordinates written by hand (or by the Geolocate button) end the pending lookup."""
        with patch('requests.get', side_effect=AssertionError("no network")):
            point = self.Point.create({'name': 'Geo Manual', 'city': 'Springfield'})
            point.write({'latitude': 1.5, 'longitude': 2.5})
        self.assertFalse(point.geo_pending)
        self.assertEqual((point.latitude, point.longitude), (1.5, 2.5))

    def test_cron_fills_coordinates(self):
        """The cron looks pending points up and stores their coordinates."""
        point = self.Point.create({'name': 'Geo Found', 'city': 'Springfield', 'country_id': self.country.id})
        with patch.object(self.PointClass, '_geocode_lookup', return_value=(39.78, -89.65)):
            self._run_cron()
        self.assertFalse(point.geo_pending)
        self.assertEqual((point.latitude, point.longitude), (39.78, -89.65))

    def test_cron_not_found_unflags(self):
        """An address that cannot be found is unflagged and left without coordinates."""
        point = self.Point.create({'name': 'Geo Unknown', 'street': 'Nowhere 0'})
        with patch.object(self.PointClass, '_geocode_lookup', return_value=None):
            self._run_cron()
        self.assertFalse(point.geo_pending)
        self.assertFalse(point.latitude)

    def test_cron_keeps_pending_when_service_down(self):
        """A network failure leaves the points queued for the next run."""
        point = self.Point.create({'name': 'Geo Down', 'city': 'Springfield'})
        with patch.object(self.PointClass, '_geocode_lookup',
                          side_effect=requests.ConnectionError("down")):
            self._run_cron()
        self.assertTrue(point.geo_pending)
