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
import datetime
import logging

from odoo import fields
from odoo.tests.common import tagged, TransactionCase


_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'wm_compliance')
class TestWmComplianceTarget(TransactionCase):
    """Unit tests verifying environmental compliance target progress calculations."""

    def setUp(self):
        """
        Set up test case preconditions and test data.
        """
        super(TestWmComplianceTarget, self).setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Target Operator Partner',
            'is_generator': True,
        })
        self.transporter = self.env['res.partner'].create({
            'name': 'Transporter Partner',
            'is_transporter': True,
        })
        self.facility = self.env['wm.disposal.facility'].create({
            'name': 'Disposal Facility',
            'facility_type': 'recycling',
        })
        self.waste_category = self.env['wm.waste.category'].create({
            'name': 'E-Waste Category',
            'code': 'E-WASTE',
        })
        self.uom = self.env.ref('uom.product_uom_kgm', raise_if_not_found=False)
        if not self.uom:
            self.uom = self.env['uom.uom'].search([], limit=1)

    def test_compliance_target_calculations(self):
        """
        Test that compliance target calculations behaves as expected.
        """
        today = fields.Date.today()
        # Create a target for partner, E-Waste category, target = 100 kg
        target = self.env['wm.compliance.target'].create({
            'partner_id': self.partner.id,
            'waste_category_id': self.waste_category.id,
            'period_start': today - datetime.timedelta(days=10),
            'period_end': today + datetime.timedelta(days=10),
            'target_quantity': 100.0,
        })

        # Initial check
        target.invalidate_recordset()
        self.assertEqual(target.achieved_quantity, 0.0)
        self.assertEqual(target.compliance_pct, 0.0)
        self.assertEqual(target.state, 'breached')

        # Create manifest in draft state: should NOT count towards target
        manifest = self.env['wm.compliance.manifest'].create({
            'generator_id': self.partner.id,
            'transporter_id': self.transporter.id,
            'disposal_facility_id': self.facility.id,
            'manifest_date': today,
            'line_ids': [
                (0, 0, {
                    'waste_category_id': self.waste_category.id,
                    'quantity': 60.0,
                    'uom_id': self.uom.id if self.uom else False,
                })
            ]
        })

        target.invalidate_recordset()
        self.assertEqual(target.achieved_quantity, 0.0)

        # Submit manifest: state moves to submitted. Now it should count!
        manifest.action_submit()

        target.invalidate_recordset()
        self.assertEqual(target.achieved_quantity, 60.0)
        self.assertEqual(target.compliance_pct, 60.0)
        self.assertEqual(target.state, 'at_risk') # between 50% and 80%

        # Add another manifest and submit to get to 85% (on track)
        manifest2 = self.env['wm.compliance.manifest'].create({
            'generator_id': self.partner.id,
            'transporter_id': self.transporter.id,
            'disposal_facility_id': self.facility.id,
            'manifest_date': today,
            'line_ids': [
                (0, 0, {
                    'waste_category_id': self.waste_category.id,
                    'quantity': 25.0,
                    'uom_id': self.uom.id if self.uom else False,
                })
            ]
        })
        manifest2.action_submit()

        target.invalidate_recordset()
        self.assertEqual(target.achieved_quantity, 85.0)
        self.assertEqual(target.compliance_pct, 85.0)
        self.assertEqual(target.state, 'on_track') # >= 80%

        _logger.info('PASS: test_compliance_target_calculations')
