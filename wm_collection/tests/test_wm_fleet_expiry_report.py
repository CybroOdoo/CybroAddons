# -*- coding: utf-8 -*-
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
import logging
from datetime import timedelta

from odoo import fields
from odoo.tests import tagged, TransactionCase


_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'wm_reporting')
class TestWmFleetExpiryReport(TransactionCase):
    """Unit tests verifying vehicle certificate and licence expiry reporting logic."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        cls.today = fields.Date.today()
        cls.expiry_in_10 = cls.today + timedelta(days=10)
        cls.expiry_in_20 = cls.today + timedelta(days=20)

        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Compactor Brand'})
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.env['fleet.vehicle.model'].create({'name': 'Compactor Model', 'brand_id': brand.id}).id,
            'license_plate': 'WM-EXP-001',
            'pollution_cert_expiry': cls.expiry_in_10,
            'insurance_expiry': cls.expiry_in_20,
        })
        cls.driver = cls.env['res.partner'].create({
            'name': 'Driver Expiry Test',
            'is_driver': True,
            'licence_expiry': cls.expiry_in_10,
        })

    def test_combined_expiry_report_union(self):
        """
        Test that combined expiry report union behaves as expected.
        """
        reports = self.env['wm.fleet.expiry.report'].search([])
        vehicle_pollution = reports.filtered(lambda r: r.entity_name == self.vehicle.name and r.document_type == 'Pollution Certificate')
        vehicle_insurance = reports.filtered(lambda r: r.entity_name == self.vehicle.name and r.document_type == 'Insurance Policy')
        driver_licence = reports.filtered(lambda r: r.entity_name == self.driver.name and r.document_type == 'Driver Licence')

        self.assertTrue(vehicle_pollution, "Vehicle pollution expiry row should exist")
        self.assertEqual(vehicle_pollution[0].days_remaining, 10)

        self.assertTrue(vehicle_insurance, "Vehicle insurance expiry row should exist")
        self.assertEqual(vehicle_insurance[0].days_remaining, 20)

        self.assertTrue(driver_licence, "Driver licence expiry row should exist")
        self.assertEqual(driver_licence[0].days_remaining, 10)
        _logger.info('PASS: test_combined_expiry_report_union')
