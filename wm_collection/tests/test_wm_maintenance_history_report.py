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

from odoo import fields
from odoo.tests import tagged, TransactionCase


_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'wm_reporting')
class TestWmMaintenanceHistoryReport(TransactionCase):
    """Unit tests verifying vehicle maintenance checklist history reporting."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Van Brand'})
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.env['fleet.vehicle.model'].create({'name': 'Van Model', 'brand_id': brand.id}).id,
            'license_plate': 'WM-MNT-001',
        })
        cls.today = fields.Date.context_today(cls)

        # Create 2 checklists: 1 checked (passed), 1 tocheck
        cls.chk1 = cls.env['wm.vehicle.maintenance.checklist'].create({
            'name': 'CHK-001',
            'vehicle_id': cls.vehicle.id,
            'checklist_type': 'pre_trip',
            'date': cls.today,
            'state': 'checked',
        })
        cls.chk2 = cls.env['wm.vehicle.maintenance.checklist'].create({
            'name': 'CHK-002',
            'vehicle_id': cls.vehicle.id,
            'checklist_type': 'post_trip',
            'date': cls.today,
            'state': 'tocheck',
        })

    def test_maintenance_history_pass_rate(self):
        """
        Test that maintenance history pass rate behaves as expected.
        """
        reports = self.env['wm.maintenance.history.report'].search([
            ('vehicle_id', '=', self.vehicle.id),
            ('date', '=', self.today)
        ])
        self.assertTrue(reports, "Maintenance history report row should be present")
        report = reports[0]
        self.assertEqual(report.total_checks, 2)
        self.assertEqual(report.passed_checks, 1)
        self.assertEqual(report.pass_rate, 50.0, "Pass rate should be 50.0%")
        _logger.info('PASS: test_maintenance_history_pass_rate')
