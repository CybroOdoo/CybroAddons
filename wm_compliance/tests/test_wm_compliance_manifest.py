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
from odoo.exceptions import UserError
from odoo.tests.common import tagged, TransactionCase


_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'wm_compliance')
class TestWmComplianceManifest(TransactionCase):
    """Unit tests verifying regulatory manifest workflows, locking, and exports."""

    def setUp(self):
        """
        Set up test case preconditions and test data.
        """
        super(TestWmComplianceManifest, self).setUp()

        self.generator = self.env['res.partner'].create({
            'name': 'Generator Partner',
            'is_generator': True,
        })
        self.transporter = self.env['res.partner'].create({
            'name': 'Transporter Partner',
            'is_transporter': True,
        })
        self.facility_no_email = self.env['wm.disposal.facility'].create({
            'name': 'Facility No Email',
            'facility_type': 'recycling',
        })
        self.facility_with_email = self.env['wm.disposal.facility'].create({
            'name': 'Facility With Email',
            'facility_type': 'recycling',
            'contact_email': 'facility@example.com',
        })

        self.waste_category = self.env['wm.waste.category'].create({
            'name': 'Test Hazardous Category Unique',
            'code': 'HAZ_TEST_UNQ',
        })
        self.uom = self.env.ref('uom.product_uom_kgm', raise_if_not_found=False)
        if not self.uom:
            self.uom = self.env['uom.uom'].search([], limit=1)

    def test_manifest_lifecycle_and_locking(self):
        # Create manifest
        """
        Test that manifest lifecycle and locking behaves as expected.
        """
        manifest = self.env['wm.compliance.manifest'].create({
            'generator_id': self.generator.id,
            'transporter_id': self.transporter.id,
            'disposal_facility_id': self.facility_no_email.id,
            'line_ids': [
                (0, 0, {
                    'waste_category_id': self.waste_category.id,
                    'quantity': 100.0,
                    'uom_id': self.uom.id if self.uom else False,
                }),
                (0, 0, {
                    'waste_category_id': self.waste_category.id,
                    'quantity': 50.0,
                    'uom_id': self.uom.id if self.uom else False,
                })
            ]
        })

        # Verify name sequence generated
        self.assertNotEqual(manifest.name, '/')
        self.assertTrue(manifest.name.startswith('MAN/'))

        # Verify total quantity compute
        self.assertEqual(manifest.total_quantity, 150.0)

        # Lifecycle: draft
        self.assertEqual(manifest.state, 'draft')

        # Submit: moves to submitted, signs, sends email (none configured, doesn't error)
        manifest.action_submit()
        self.assertEqual(manifest.state, 'submitted')
        self.assertTrue(manifest.signature_id)
        self.assertTrue(manifest.signature_id.hash_verified)

        # Collect
        manifest.action_collect()
        self.assertEqual(manifest.state, 'collected')

        # Dispose
        manifest.action_dispose()
        self.assertEqual(manifest.state, 'disposed')

        # Verify immutable locking at terminal 'disposed' state
        with self.assertRaises(UserError):
            manifest.write({'manifest_date': fields.Date.today()})
        with self.assertRaises(UserError):
            manifest.unlink()

        _logger.info('PASS: test_manifest_lifecycle_and_locking')

    def test_export_and_notify_email_sending(self):
        # Create manifest with facility email
        """
        Test that export and notify email sending behaves as expected.
        """
        manifest = self.env['wm.compliance.manifest'].create({
            'generator_id': self.generator.id,
            'transporter_id': self.transporter.id,
            'disposal_facility_id': self.facility_with_email.id,
            'line_ids': [
                (0, 0, {
                    'waste_category_id': self.waste_category.id,
                    'quantity': 20.0,
                    'uom_id': self.uom.id if self.uom else False,
                })
            ]
        })

        # Run submit which triggers export and email notification
        manifest.action_submit()

        # Check if mail.mail was created and contains the attachment
        mail = self.env['mail.mail'].search([
            ('email_to', '=', 'facility@example.com'),
            ('subject', 'like', 'Signed Waste Manifest')
        ], limit=1)
        self.assertTrue(mail)
        self.assertEqual(len(mail.attachment_ids), 1)
        self.assertEqual(mail.attachment_ids[0].id, manifest.signature_id.pdf_attachment_id.id)

        _logger.info('PASS: test_export_and_notify_email_sending')
