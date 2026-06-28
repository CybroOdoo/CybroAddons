# -*- coding: utf-8 -*-

import logging

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestResConfigSettings(TransactionCase):

    def test_set_values_valid(self):
        """Test valid settings values"""

        _logger.info("=== VALID SETTINGS TEST STARTED ===")

        settings = self.env['res.config.settings'].create({
            'limit': 5,
            'status': 'purchase_order',
        })

        settings.set_values()

        limit = self.env['ir.config_parameter'].sudo().get_param(
            'purchase_product_history.limit'
        )

        status = self.env['ir.config_parameter'].sudo().get_param(
            'purchase_product_history.status'
        )

        _logger.info("Saved Limit: %s", limit)
        _logger.info("Saved Status: %s", status)

        self.assertEqual(limit, '5')
        self.assertEqual(status, 'purchase_order')

        _logger.info("=== VALID SETTINGS TEST PASSED ===")

    def test_set_values_negative_limit(self):
        """Test validation for negative limit"""

        _logger.info("=== NEGATIVE LIMIT TEST STARTED ===")

        settings = self.env['res.config.settings'].create({
            'limit': -1,
            'status': 'all',
        })

        with self.assertRaises(ValidationError):
            settings.set_values()

        _logger.info("ValidationError Raised Successfully")

        _logger.info("=== NEGATIVE LIMIT TEST PASSED ===")