# -*- coding: utf-8 -*-
from odoo.tests.common import tagged
from .common import TestConsignmentCommon


@tagged('post_install', '-at_install')
class TestResConfigSettings(TestConsignmentCommon):

    def test_settings_domain_and_defaults(self):
        """Test default config methods and default locations."""
        # Test settings domain
        self.assertEqual(self.env['sale.consignment']._settings_domain(), 'True')

        # Test default destination
        self.assertEqual(self.env['sale.consignment']._default_destination(), self.location_dest.id)
