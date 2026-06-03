# -*- coding: utf-8 -*-
from types import SimpleNamespace
from unittest.mock import patch

from odoo.addons.advanced_tender_management.controllers.portal import PortalController

from .common import TenderManagementTestCommon


class TestPortalController(TenderManagementTestCommon):
    """Tests for portal tender page controller."""

    def test_portal_my_tenders_renders_current_vendor_bids(self):
        tender = self.create_tender()
        bid = self.create_bid(tender, self.vendor_1)
        rendered = {}
        dummy_request = SimpleNamespace(
            env=self.env(user=self.env.uid),
            render=lambda template, values: rendered.update({
                'template': template,
                'values': values,
            }) or rendered,
        )
        dummy_request.env.user = SimpleNamespace(partner_id=self.vendor_1)
        controller = PortalController()

        with patch('odoo.addons.advanced_tender_management.controllers.portal.request', dummy_request):
            result = controller.portal_my_tenders()

        self.assertEqual(result['template'], 'advanced_tender_management.portal_my_tenders')
        self.assertEqual(result['values']['bid_records'], bid)
