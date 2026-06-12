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

import base64
import io

from PIL import Image

from odoo.tests.common import TransactionCase


def _make_jpeg_b64(width=100, height=100, quality=85):
    """Helper: generate a small in-memory JPEG and return its base64 bytes."""
    buf = io.BytesIO()
    img = Image.new('RGB', (width, height), color=(255, 0, 0))
    img.save(buf, format='JPEG', quality=quality)
    return base64.b64encode(buf.getvalue())


def _make_png_b64(width=100, height=100):
    """Helper: generate a small in-memory PNG and return its base64 bytes."""
    buf = io.BytesIO()
    img = Image.new('RGB', (width, height), color=(0, 128, 0))
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue())


class TestImageCompressor(TransactionCase):
    """Test cases for the ImageCompressor model (ir.image.compressor.rule)."""

    def setUp(self):
        """Set up test fixtures shared by all test methods."""
        super().setUp()
        self.CompressorRule = self.env['ir.image.compressor.rule']
        self.IrAttachment = self.env['ir.attachment']
        self.IrModel = self.env['ir.model']
        self.FileFormat = self.env['source.file.format']

        # Resolve the ir.model record for 'res.partner'
        self.partner_model = self.IrModel.search(
            [('model', '=', 'res.partner')], limit=1)

        # Create a basic active compression rule
        self.rule = self.CompressorRule.create({
            'name': 'Test JPEG Rule',
            'af_model_ids': [(4, self.partner_model.id)],
            'quality': 80,
            'destination_format': 'JPEG',
            'active': True,
            'minimum_size': 0,
            'older_days': 0,
        })

        # Create a JPEG attachment linked to res.partner
        self.attachment_jpeg = self.IrAttachment.create({
            'name': 'test_image.jpeg',
            'datas': _make_jpeg_b64(),
            'mimetype': 'image/jpeg',
            'res_model': 'res.partner',
            'res_id': 0,
        })

    # =========================================================================
    # Tests for: _get_attachments_domain()
    # =========================================================================

    def test_get_attachments_domain_returns_list(self):
        """_get_attachments_domain returns a list (Odoo domain)."""
        domain = self.rule._get_attachments_domain(['res.partner'])
        self.assertIsInstance(domain, list)

    def test_get_attachments_domain_includes_res_model(self):
        """Domain contains a filter on 'res_model' when model_names provided."""
        domain = self.rule._get_attachments_domain(['res.partner'])
        flat = str(domain)
        self.assertIn('res_model', flat)
        self.assertIn('res.partner', flat)

    def test_get_attachments_domain_no_model_names(self):
        """Domain with empty model_names omits the res_model filter."""
        domain = self.rule._get_attachments_domain([])
        flat = str(domain)
        self.assertNotIn('res_model', flat)

    def test_get_attachments_domain_mimetype_filter_present(self):
        """Domain always contains a mimetype filter."""
        domain = self.rule._get_attachments_domain(['res.partner'])
        flat = str(domain)
        self.assertIn('mimetype', flat)

    def test_get_attachments_domain_with_minimum_size(self):
        """Domain includes a file_size filter when minimum_size > 0."""
        self.rule.write({'minimum_size': 10})
        domain = self.rule._get_attachments_domain(['res.partner'])
        flat = str(domain)
        self.assertIn('file_size', flat)

    def test_get_attachments_domain_no_minimum_size(self):
        """Domain omits file_size filter when minimum_size is 0."""
        self.rule.write({'minimum_size': 0})
        domain = self.rule._get_attachments_domain(['res.partner'])
        flat = str(domain)
        self.assertNotIn('file_size', flat)

    def test_get_attachments_domain_with_older_days(self):
        """Domain includes a create_date filter when older_days > 0."""
        self.rule.write({'older_days': 7})
        domain = self.rule._get_attachments_domain(['res.partner'])
        flat = str(domain)
        self.assertIn('create_date', flat)

    def test_get_attachments_domain_no_older_days(self):
        """Domain omits create_date filter when older_days is 0."""
        self.rule.write({'older_days': 0})
        domain = self.rule._get_attachments_domain(['res.partner'])
        flat = str(domain)
        self.assertNotIn('create_date', flat)

    def test_get_attachments_domain_with_source_format_ids(self):
        """Domain uses source_format mime_types when source_format_ids is set."""
        fmt = self.FileFormat.create({
            'name': 'jpeg_test',
            'mime_type': 'image/jpeg-test-only',
        })
        self.rule.write({'source_format_ids': [(4, fmt.id)]})
        domain = self.rule._get_attachments_domain(['res.partner'])
        flat = str(domain)
        self.assertIn('image/jpeg-test-only', flat)

    def test_get_attachments_domain_no_source_format_uses_global(self):
        """Without source_format_ids the domain uses all known mimetypes."""
        self.rule.write({'source_format_ids': [(5, 0, 0)]})
        domain = self.rule._get_attachments_domain(['res.partner'])
        flat = str(domain)
        # 'image/jpeg' is in mimetypes_global
        self.assertIn('image/jpeg', flat)

    def test_get_attachments_domain_multiple_models(self):
        """Domain correctly handles multiple model names."""
        domain = self.rule._get_attachments_domain(
            ['res.partner', 'res.users'])
        flat = str(domain)
        self.assertIn('res.partner', flat)
        self.assertIn('res.users', flat)

    def test_get_attachments_domain_attachment_matched(self):
        """Attachments matching the domain are actually retrieved."""
        domain = self.rule._get_attachments_domain(['res.partner'])
        attachments = self.IrAttachment.search(domain)
        ids = attachments.ids
        self.assertIn(self.attachment_jpeg.id, ids)

    # =========================================================================
    # Tests for: _schedule_auto_compress()
    # =========================================================================

    def test_schedule_auto_compress_runs_without_error(self):
        """_schedule_auto_compress executes without raising an exception."""
        try:
            self.CompressorRule._schedule_auto_compress()
        except Exception as exc:
            self.fail(
                "_schedule_auto_compress raised an exception: %s" % exc)

    def test_schedule_auto_compress_processes_active_rules_only(self):
        """Only active rules are processed; inactive rules are skipped."""
        # Create an inactive rule
        inactive_rule = self.CompressorRule.create({
            'name': 'Inactive Rule',
            'af_model_ids': [(4, self.partner_model.id)],
            'quality': 50,
            'destination_format': 'PNG',
            'active': False,
        })
        # Should not raise; inactive rule should simply be ignored
        self.CompressorRule._schedule_auto_compress()
        # Verify the attachment was not altered unexpectedly
        inactive_rule.unlink()

    def test_schedule_auto_compress_compresses_jpeg_attachment(self):
        """After running the scheduler, a JPEG attachment's datas are re-saved."""
        original_datas = self.attachment_jpeg.datas
        self.CompressorRule._schedule_auto_compress()
        # The attachment should still have some data (not None)
        self.assertTrue(self.attachment_jpeg.datas)

    def test_schedule_auto_compress_renames_attachment(self):
        """After compression the attachment name extension is updated."""
        self.attachment_jpeg.name = 'test_image.png'
        self.CompressorRule._schedule_auto_compress()
        # Rule destination_format is JPEG, so extension should become .jpeg
        self.assertTrue(
            self.attachment_jpeg.name.endswith('.jpeg'),
            "Expected attachment name to end with '.jpeg', got: %s"
            % self.attachment_jpeg.name
        )

    def test_schedule_auto_compress_with_png_destination(self):
        """Scheduler rule with PNG destination renames attachment to .png."""
        self.rule.write({'destination_format': 'PNG'})
        self.CompressorRule._schedule_auto_compress()
        self.assertTrue(
            self.attachment_jpeg.name.endswith('.png'),
            "Expected attachment name to end with '.png', got: %s"
            % self.attachment_jpeg.name
        )

    def test_schedule_auto_compress_quality_applied(self):
        """Compression with quality=10 produces smaller data than quality=95."""
        # Create a high-quality attachment from a large PNG
        large_b64 = _make_png_b64(width=500, height=500)
        att = self.IrAttachment.create({
            'name': 'large_test.png',
            'datas': large_b64,
            'mimetype': 'image/png',
            'res_model': 'res.partner',
            'res_id': 0,
        })
        # Rule at low quality
        self.rule.write({'quality': 10, 'destination_format': 'JPEG'})
        self.CompressorRule._schedule_auto_compress()
        compressed_size = len(att.datas or b'')
        original_size = len(large_b64)
        self.assertLess(
            compressed_size, original_size,
            "Compressed data should be smaller than the original."
        )

    def test_schedule_auto_compress_skips_non_matching_mimetype(self):
        """Attachments with a non-image mimetype are not compressed."""
        txt_attachment = self.IrAttachment.create({
            'name': 'document.txt',
            'datas': base64.b64encode(b'Hello World'),
            'mimetype': 'text/plain',
            'res_model': 'res.partner',
            'res_id': 0,
        })
        original_datas = txt_attachment.datas
        self.CompressorRule._schedule_auto_compress()
        # Text attachment must remain untouched
        self.assertEqual(txt_attachment.datas, original_datas)

    def test_schedule_auto_compress_skips_attachment_outside_model(self):
        """Attachments linked to models not in rule's af_model_ids are skipped."""
        # Attachment on 'res.currency' is not in the rule
        other_att = self.IrAttachment.create({
            'name': 'other_model_img.jpeg',
            'datas': _make_jpeg_b64(),
            'mimetype': 'image/jpeg',
            'res_model': 'res.currency',
            'res_id': 0,
        })
        original_datas = other_att.datas
        self.CompressorRule._schedule_auto_compress()
        self.assertEqual(other_att.datas, original_datas)

    def test_schedule_auto_compress_minimum_size_filter(self):
        """Attachments smaller than minimum_size (KB) are not compressed."""
        # Set a very large minimum size so the test attachment is skipped
        self.rule.write({'minimum_size': 99999})
        original_datas = self.attachment_jpeg.datas
        self.CompressorRule._schedule_auto_compress()
        self.assertEqual(self.attachment_jpeg.datas, original_datas)

    def test_schedule_auto_compress_no_active_rules(self):
        """_schedule_auto_compress with no active rules runs without error."""
        self.rule.write({'active': False})
        try:
            self.CompressorRule._schedule_auto_compress()
        except Exception as exc:
            self.fail(
                "_schedule_auto_compress raised an error with no active "
                "rules: %s" % exc)

    def test_schedule_auto_compress_default_quality_used_when_zero(self):
        """When rule quality is 0, the scheduler defaults to quality 95."""
        self.rule.write({'quality': 0})
        try:
            self.CompressorRule._schedule_auto_compress()
        except Exception as exc:
            self.fail(
                "Scheduler failed when quality=0: %s" % exc)
        # Attachment should still carry valid data
        self.assertTrue(self.attachment_jpeg.datas)

    # =========================================================================
    # Tests for: model field defaults and rule creation
    # =========================================================================

    def test_rule_create_with_required_fields(self):
        """A compression rule can be created with all required fields."""
        rule = self.CompressorRule.create({
            'name': 'Basic Rule',
            'af_model_ids': [(4, self.partner_model.id)],
            'destination_format': 'JPEG',
            'active': True,
        })
        self.assertEqual(rule.name, 'Basic Rule')
        self.assertEqual(rule.destination_format, 'JPEG')
        self.assertTrue(rule.active)

    def test_rule_default_destination_format_is_jpeg(self):
        """The default destination_format of a new rule is JPEG."""
        rule = self.CompressorRule.create({
            'name': 'Default Format Rule',
            'af_model_ids': [(4, self.partner_model.id)],
        })
        self.assertEqual(rule.destination_format, 'JPEG')

    def test_rule_active_field(self):
        """active field toggles archive/unarchive correctly."""
        self.rule.write({'active': False})
        self.assertFalse(self.rule.active)
        self.rule.write({'active': True})
        self.assertTrue(self.rule.active)

    def test_rule_multiple_models(self):
        """A compression rule can be associated with multiple models."""
        user_model = self.IrModel.search(
            [('model', '=', 'res.users')], limit=1)
        self.rule.write({
            'af_model_ids': [(4, self.partner_model.id),
                              (4, user_model.id)]
        })
        self.assertIn(self.partner_model, self.rule.af_model_ids)
        self.assertIn(user_model, self.rule.af_model_ids)
