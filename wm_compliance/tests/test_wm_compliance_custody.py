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

from odoo.exceptions import UserError
from odoo.tests.common import tagged, TransactionCase


_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'wm_compliance')
class TestWmComplianceCustody(TransactionCase):
    """Unit tests verifying chain-of-custody transfer logging and custodian assignments."""

    def setUp(self):
        """
        Set up test case preconditions and test data.
        """
        super(TestWmComplianceCustody, self).setUp()
        self.generator = self.env['res.partner'].create({
            'name': 'Generator Partner',
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
        self.manifest = self.env['wm.compliance.manifest'].create({
            'generator_id': self.generator.id,
            'transporter_id': self.transporter.id,
            'disposal_facility_id': self.facility.id,
        })

    def test_custody_append_only_operations(self):
        # Create custody log entry in draft
        """
        Test that custody append only operations behaves as expected.
        """
        custody = self.env['wm.compliance.custody'].create({
            'manifest_id': self.manifest.id,
            'action': 'generated',
            'location': 'Warehouse A',
            'notes': 'Initial batch',
        })
        self.assertEqual(custody.action, 'generated')
        self.assertEqual(custody.location, 'Warehouse A')

        # In draft state, updating notes or location is allowed
        custody.write({'location': 'Warehouse A - Bay 2'})
        self.assertEqual(custody.location, 'Warehouse A - Bay 2')

        # Submit manifest: state moves to submitted
        self.manifest.action_submit()

        # Once active, write raises UserError
        with self.assertRaises(UserError):
            custody.write({'location': 'Warehouse B'})

        # Once active, unlink raises UserError
        with self.assertRaises(UserError):
            custody.unlink()

        _logger.info('PASS: test_custody_append_only_operations')
