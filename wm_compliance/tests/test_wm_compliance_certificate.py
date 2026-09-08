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
class TestWmComplianceCertificate(TransactionCase):
    """Unit tests verifying compliance certificate generation and SHA-256 hash digests."""

    def setUp(self):
        """
        Set up test case preconditions and test data.
        """
        super(TestWmComplianceCertificate, self).setUp()
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
        self.uom = self.env.ref('uom.product_uom_kgm', raise_if_not_found=False)
        if not self.uom:
            self.uom = self.env['uom.uom'].search([], limit=1)

    def test_certificate_with_and_without_manifest(self):
        # 1. Without manifest
        """
        Test that certificate with and without manifest behaves as expected.
        """
        cert_no_manifest = self.env['wm.compliance.certificate'].create({
            'name': 'Stand-alone Recycling Certificate',
            'certificate_type': 'recycling',
            'facility_id': self.facility.id,
            'quantity': 500.0,
            'uom_id': self.uom.id if self.uom else False,
            'certificate_no': 'CERT-STANDALONE-001',
        })
        self.assertEqual(cert_no_manifest.name, 'Stand-alone Recycling Certificate')
        self.assertFalse(cert_no_manifest.manifest_id)
        self.assertEqual(cert_no_manifest.state, 'draft')

        # Issue standalone certificate
        cert_no_manifest.action_issue()
        self.assertEqual(cert_no_manifest.state, 'issued')
        self.assertTrue(cert_no_manifest.signature_id)

        # 2. With manifest
        cert_with_manifest = self.env['wm.compliance.certificate'].create({
            'name': 'Manifest Linked Certificate',
            'certificate_type': 'disposal',
            'facility_id': self.facility.id,
            'quantity': 150.0,
            'uom_id': self.uom.id if self.uom else False,
            'certificate_no': 'CERT-MANIFEST-002',
            'manifest_id': self.manifest.id,
        })
        self.assertEqual(cert_with_manifest.manifest_id.id, self.manifest.id)

        # Issue
        cert_with_manifest.action_issue()
        self.assertEqual(cert_with_manifest.state, 'issued')

        # Test locked at issued state
        with self.assertRaises(UserError):
            cert_with_manifest.write({'quantity': 200.0})
        with self.assertRaises(UserError):
            cert_with_manifest.unlink()

        _logger.info('PASS: test_certificate_with_and_without_manifest')
