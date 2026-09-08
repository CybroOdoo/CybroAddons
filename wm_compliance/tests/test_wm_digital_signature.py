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
import base64
import hashlib
import logging

from odoo.exceptions import UserError
from odoo.tests.common import tagged, TransactionCase


_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'wm_compliance')
class TestWmDigitalSignature(TransactionCase):
    """Unit tests verifying digital signature verification and tamper detection."""

    def setUp(self):
        """
        Set up test case preconditions and test data.
        """
        super(TestWmDigitalSignature, self).setUp()

        # We can use any dummy record to sign (e.g. res.partner)
        self.dummy_record = self.env['res.partner'].create({
            'name': 'Sign Partner Test',
        })

    def test_signature_hash_and_verification(self):
        """
        Test that signature hash and verification behaves as expected.
        """
        pdf_bytes = b"PDF dummy content data representation string"
        expected_hash = hashlib.sha256(pdf_bytes).hexdigest()

        # Sign
        sig = self.env['wm.digital.signature'].sign_document(
            record=self.dummy_record,
            pdf_bytes=pdf_bytes,
            filename='test_signed.pdf'
        )

        # Verify hash match
        self.assertEqual(sig.pdf_hash, expected_hash)

        # Check computed verification
        sig._compute_hash_verified()
        self.assertTrue(sig.hash_verified)

        # Verify immediate lock: no edits allowed
        with self.assertRaises(UserError):
            sig.write({'pdf_hash': 'badhash123'})

        with self.assertRaises(UserError):
            sig.unlink()

        _logger.info('PASS: test_signature_hash_and_verification')

    def test_tampering_detection(self):
        """
        Test that tampering detection behaves as expected.
        """
        pdf_bytes = b"Original Document Content"
        sig = self.env['wm.digital.signature'].sign_document(
            record=self.dummy_record,
            pdf_bytes=pdf_bytes,
            filename='original.pdf'
        )

        sig._compute_hash_verified()
        self.assertTrue(sig.hash_verified)

        # Tamper with the raw attachment content directly
        attachment = sig.pdf_attachment_id

        # Odoo 19 uses raw, but let's overwrite it with raw/datas
        attachment.write({
            'raw': b"Tampered Document Content",
            'datas': base64.b64encode(b"Tampered Document Content"),
        })

        # Re-compute verification: must fail!
        sig.invalidate_recordset()
        sig._compute_hash_verified()
        self.assertFalse(sig.hash_verified)

        _logger.info('PASS: test_tampering_detection')
