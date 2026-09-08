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
"""
Smoke tests verifying complete removal of stream classification:
  - compliance_stream removed from wm.waste.category
  - stream / stream_summary removed from wm.compliance.manifest
  - Manifest lifecycle operates normally without stream fields
"""
import logging

from odoo.tests.common import tagged, TransactionCase


_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'wm_compliance')
class TestStreamRemoval(TransactionCase):
    """Unit tests verifying waste stream line derivation and removal behaviors."""

    def setUp(self):
        """
        Set up test case preconditions and test data.
        """
        super().setUp()
        self.generator = self.env['res.partner'].create({
            'name': 'Test Generator Partner',
            'is_generator': True,
        })
        self.transporter = self.env['res.partner'].create({
            'name': 'Test Transporter Partner',
            'is_transporter': True,
        })
        self.facility = self.env['wm.disposal.facility'].create({
            'name': 'Test Disposal Facility',
            'facility_type': 'recycling',
        })
        self.category = self.env['wm.waste.category'].create({
            'name': 'General Test Category',
            'code': 'GTC01',
        })

    def test_stream_fields_removed(self):
        """
        Verify stream fields do not exist on category or manifest models.
        """
        self.assertNotIn('compliance_stream', self.env['wm.waste.category']._fields)
        self.assertNotIn('stream', self.env['wm.compliance.manifest']._fields)
        self.assertNotIn('stream_summary', self.env['wm.compliance.manifest']._fields)

    def test_manifest_lifecycle_without_stream(self):
        """
        Verify creating and submitting manifest works without stream fields.
        """
        manifest = self.env['wm.compliance.manifest'].create({
            'generator_id': self.generator.id,
            'transporter_id': self.transporter.id,
            'disposal_facility_id': self.facility.id,
            'line_ids': [(0, 0, {
                'waste_category_id': self.category.id,
                'quantity': 25.0,
            })]
        })
        self.assertEqual(manifest.state, 'draft')
        self.assertEqual(manifest.total_quantity, 25.0)

        # Submit manifest
        manifest.action_submit()
        self.assertEqual(manifest.state, 'submitted')
