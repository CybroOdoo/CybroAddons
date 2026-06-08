# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
# -*- coding: utf-8 -*-
import logging

from odoo.tests import common
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class TestImageCompression(common.TransactionCase):

    def setUp(self):
        super(TestImageCompression, self).setUp()

        _logger.info("========== START setUp: TestImageCompression ==========")

        self.FileFormatSource = self.env['source.file.format']
        self.ImageCompressorRule = self.env['ir.image.compressor.rule']
        self.IrAttachment = self.env['ir.attachment']

        _logger.info("Model references initialized successfully")

        # Dummy Base64 Image (1x1 transparent PNG)
        self.dummy_image_b64 = b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='

        _logger.info("Dummy base64 image prepared")

        self.png_format = self.FileFormatSource.create({
            'name': 'png',
            'mime_type': 'image/png'
        })

        _logger.info(
            "Created PNG source format -> ID: %s | Name: %s",
            self.png_format.id,
            self.png_format.name
        )

        self.jpeg_format = self.FileFormatSource.create({
            'name': 'jpeg',
            'mime_type': 'image/jpeg'
        })

        _logger.info(
            "Created JPEG source format -> ID: %s | Name: %s",
            self.jpeg_format.id,
            self.jpeg_format.name
        )

        self.ir_model_attachment = self.env['ir.model'].search(
            [('model', '=', 'ir.attachment')],
            limit=1
        )

        _logger.info(
            "Fetched ir.model for ir.attachment -> ID: %s",
            self.ir_model_attachment.id
        )

        _logger.info("========== SUCCESS setUp: TestImageCompression ==========")

    def test_file_format_name_get(self):
        """Test name_get of source.file.format"""

        _logger.info("========== START test_file_format_name_get ==========")

        name = self.png_format.name_get()[0][1]

        _logger.info(
            "Computed name_get value -> %s",
            name
        )

        self.assertEqual(
            name,
            "png (image/png)"
        )

        _logger.info("Display name validated successfully")

        _logger.info("========== SUCCESS test_file_format_name_get ==========")

    def test_image_compression_rule_constraints(self):
        """Test the quality constraints for image compression rules"""

        _logger.info("========== START test_image_compression_rule_constraints ==========")

        rule = self.ImageCompressorRule.create({
            'name': 'Test Quality Rule',
            'af_model_ids': [(6, 0, self.ir_model_attachment.ids)],
            'destination_format': 'JPEG',
            'quality': 100
        })

        _logger.info(
            "Created compression rule -> ID: %s | Quality: %s",
            rule.id,
            rule.quality
        )

        # Force lowercase for constraint testing
        rule.destination_format = 'jpeg'

        _logger.info(
            "Updated destination format to lowercase for constraint validation"
        )

        with self.assertRaises(ValidationError):
            _logger.info(
                "Executing constraint check expecting ValidationError for quality=100"
            )
            rule._check_reconcile()

        _logger.info("ValidationError raised successfully for invalid quality")

        rule.quality = 95

        _logger.info(
            "Updated quality to valid value -> %s",
            rule.quality
        )

        # Should not raise exception
        rule._check_reconcile()

        _logger.info("Constraint validation passed successfully for quality=95")

        _logger.info("========== SUCCESS test_image_compression_rule_constraints ==========")

    def test_get_attachments_domain(self):
        """Test the domain builder logic for attachments based on rule parameters"""

        _logger.info("========== START test_get_attachments_domain ==========")

        rule = self.ImageCompressorRule.create({
            'name': 'Test Domain Rule',
            'af_model_ids': [(6, 0, self.ir_model_attachment.ids)],
            'source_format_ids': [(6, 0, self.png_format.ids)],
            'minimum_size': 10,
            'older_days': 5,
            'allow_recompress': False,
        })

        _logger.info(
            "Created domain rule -> ID: %s",
            rule.id
        )

        domain = rule._get_attachments_domain(['ir.attachment'])

        _logger.info("Generated attachment domain -> %s", domain)

        # Check components of the domain
        domain_str = str(domain)

        self.assertIn(
            "('mimetype', 'in', ['image/png'])",
            domain_str
        )

        self.assertIn(
            "('res_model', 'in', ['ir.attachment'])",
            domain_str
        )

        self.assertIn(
            "('file_size', '>', 10240)",
            domain_str
        )  # 10 KB in bytes

        self.assertIn(
            "('is_compressed', '=', False)",
            domain_str
        )

        _logger.info("All expected domain conditions verified successfully")

        _logger.info("========== SUCCESS test_get_attachments_domain ==========")

    def test_schedule_auto_compress(self):
        """Test the auto compression schedule method"""

        _logger.info("========== START test_schedule_auto_compress ==========")

        rule = self.ImageCompressorRule.create({
            'name': 'Auto Compress Test Rule',
            'af_model_ids': [(6, 0, self.ir_model_attachment.ids)],
            'destination_format': 'JPEG',
            'quality': 50,
            'active': True,
        })

        _logger.info(
            "Created auto compression rule -> ID: %s | Quality: %s",
            rule.id,
            rule.quality
        )

        # Create a test attachment
        attachment = self.IrAttachment.create({
            'name': 'test_image.png',
            'datas': self.dummy_image_b64,
            'res_model': 'ir.attachment',
            'res_id': 0,
            'mimetype': 'image/png'
        })

        _logger.info(
            "Created attachment -> ID: %s | Name: %s | Mimetype: %s",
            attachment.id,
            attachment.name,
            attachment.mimetype
        )

        _logger.info("Executing scheduled auto compression")

        # Execute the auto-compress job
        self.ImageCompressorRule._schedule_auto_compress()

        _logger.info("Auto compression execution completed")

        # Re-fetch attachment to check modifications
        attachment.invalidate_recordset()

        _logger.info(
            "Attachment after compression -> Name: %s",
            attachment.name
        )

        # Name should be modified to have the new extension
        self.assertTrue(
            attachment.name.endswith('.jpeg')
        )

        _logger.info("Verified attachment extension changed to .jpeg")

        _logger.info("========== SUCCESS test_schedule_auto_compress ==========")
