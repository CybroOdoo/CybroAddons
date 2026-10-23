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
#############################################################################
from unittest.mock import MagicMock, patch

from odoo.http import Response
from odoo.tests import tagged

from odoo.addons.website_order_delivery_tracking.controllers import (
    website_order_delivery_tracking as controller_module)

from .common import DeliveryTrackingCommon


@tagged('post_install', '-at_install')
class TestTrackingController(DeliveryTrackingCommon):
    """Test the controller methods directly, with a mocked request.

    No HTTP server is involved, so the tests run inside the test transaction
    and do not depend on ports, sessions or other running Odoo instances.
    """

    def setUp(self):
        super().setUp()
        self.controller = controller_module.Tracking()
        self.request = MagicMock()
        self.request.env = self.env
        # The route wrapper only accepts real responses.
        self.request.render.return_value = Response('rendered')
        patcher = patch.object(controller_module, 'request', self.request)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _search(self, tracking_ref):
        return self.controller.input_data_processing(input_data=tracking_ref)

    def _edit(self, **params):
        return self.controller.track_data_edit(**params)

    # ------------------------------------------------------------------
    # /tracking/details
    # ------------------------------------------------------------------
    def test_tracking_page_renders_template(self):
        """The page route renders the tracking template."""
        self.controller.get_track_details()
        self.request.render.assert_called_once_with(
            'website_order_delivery_tracking.tracking_template')
        self.assertTrue(self.env.ref(
            'website_order_delivery_tracking.tracking_template'))

    # ------------------------------------------------------------------
    # /tracking/details/update
    # ------------------------------------------------------------------
    def test_search_returns_picking_details(self):
        """The search returns reference, origin, carrier and status."""
        self.picking.tracking_status = 'Out for delivery'
        self.assertEqual(self._search('TRACK-001'), [[
            self.picking.name, 'S-TRACK-001', 'Tracking Test Carrier',
            'Out for delivery',
        ]])

    def test_search_shows_default_status(self):
        """Without a status, a default message is returned."""
        self.assertEqual(
            self._search('TRACK-001')[0][3], 'Status currently not available')

    def test_search_returns_all_pickings_with_same_reference(self):
        """Every picking with the tracking reference is returned."""
        self._create_picking(origin='S-TRACK-002', tracking_ref='TRACK-001')
        result = self._search('TRACK-001')
        self.assertEqual(
            sorted(row[1] for row in result), ['S-TRACK-001', 'S-TRACK-002'])

    def test_search_unknown_reference(self):
        """An unknown tracking reference returns nothing."""
        self.assertEqual(self._search('DOES-NOT-EXIST'), [])

    def test_search_without_reference_returns_nothing(self):
        """An empty search must not list the pickings without a reference."""
        self._create_picking(origin='S-NO-REF')
        self.assertEqual(self._search(''), [])
        self.assertEqual(self._search(False), [])
        self.assertEqual(self.controller.input_data_processing(), [])

    def test_search_without_origin_or_carrier(self):
        """Missing origin and carrier are returned as empty text."""
        self._create_picking(tracking_ref='TRACK-NO-ORIGIN', carrier=False)
        result = self._search('TRACK-NO-ORIGIN')
        self.assertEqual(result[0][1:3], ['', ''])

    # ------------------------------------------------------------------
    # /tracking/details/edit
    # ------------------------------------------------------------------
    def test_edit_with_correct_api_key(self):
        """A delivery partner can update the status with the API key."""
        result = self._edit(
            api_key=self.API_KEY, tracking_number='TRACK-001',
            tracking_status='Delivered')
        self.assertEqual(result, 'Delivered')
        self.assertEqual(self.picking.tracking_status, 'Delivered')

    def test_edit_updates_all_pickings_with_same_reference(self):
        """Every picking with the tracking reference gets the new status."""
        other = self._create_picking(
            origin='S-TRACK-002', tracking_ref='TRACK-001')
        self._edit(
            api_key=self.API_KEY, tracking_number='TRACK-001',
            tracking_status='In transit')
        self.assertEqual(self.picking.tracking_status, 'In transit')
        self.assertEqual(other.tracking_status, 'In transit')

    def test_edit_with_wrong_api_key(self):
        """A wrong API key does not change the status."""
        result = self._edit(
            api_key='wrong-key', tracking_number='TRACK-001',
            tracking_status='Delivered')
        self.assertEqual(result, [])
        self.assertFalse(self.picking.tracking_status)

    def test_edit_without_api_key(self):
        """A request without an API key does not change the status."""
        result = self._edit(
            tracking_number='TRACK-001', tracking_status='Delivered')
        self.assertEqual(result, [])
        self.assertFalse(self.picking.tracking_status)

    def test_edit_with_unknown_tracking_number(self):
        """An unknown tracking number returns nothing."""
        result = self._edit(
            api_key=self.API_KEY, tracking_number='DOES-NOT-EXIST',
            tracking_status='Delivered')
        self.assertEqual(result, [])

    def test_edit_without_tracking_number_changes_nothing(self):
        """No tracking number must not update the pickings without one."""
        untracked = self._create_picking(origin='S-NO-REF')
        result = self._edit(api_key=self.API_KEY, tracking_status='Delivered')
        self.assertEqual(result, [])
        self.assertFalse(untracked.tracking_status)

    def test_edit_when_api_key_is_not_configured(self):
        """With no API key configured, nobody can update the status."""
        self.env['ir.config_parameter'].sudo().set_str(self.API_KEY_PARAM, '')
        result = self._edit(
            api_key='', tracking_number='TRACK-001',
            tracking_status='Delivered')
        self.assertEqual(result, [])
        self.assertFalse(self.picking.tracking_status)

    def test_edit_status_is_visible_in_search(self):
        """The status written by the partner is shown by the search."""
        self._edit(
            api_key=self.API_KEY, tracking_number='TRACK-001',
            tracking_status='Delivered')
        self.assertEqual(self._search('TRACK-001')[0][3], 'Delivered')
