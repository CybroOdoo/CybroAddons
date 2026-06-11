# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import base64
from datetime import datetime, timedelta
from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestImageCompressionRule(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_model = cls.env['ir.model']._get('res.partner')
        cls.source_format = cls.env['source.file.format'].create({
            'name': '.webp',
            'mime_type': 'image/webp',
        })

    def _create_rule(self, **vals):
        defaults = {
            'name': 'Compress Partner Images',
            'af_model_ids': [(6, 0, [self.partner_model.id])],
            'quality': 80,
            'destination_format': 'JPEG',
            'active': True,
        }
        defaults.update(vals)
        return self.env['ir.image.compressor.rule'].create(defaults)

    def _create_attachment(self, *, name, payload, mimetype, res_model='res.partner'):
        return self.env['ir.attachment'].create({
            'name': name,
            'type': 'binary',
            'datas': base64.b64encode(payload),
            'mimetype': mimetype,
            'res_model': res_model,
            'res_id': self.env.user.partner_id.id,
        })

    def _set_create_date(self, attachment, dt):
        self.env.cr.execute(
            "UPDATE ir_attachment SET create_date = %s WHERE id = %s",
            (dt, attachment.id),
        )
        attachment.invalidate_recordset(['create_date'])

    def test_get_attachments_domain_filters_by_all_rule_criteria(self):
        rule = self._create_rule(
            minimum_size=1,
            older_days=3,
            source_format_ids=[(6, 0, [self.source_format.id])],
        )
        old_enough = datetime.now() - timedelta(days=5)

        matching = self._create_attachment(
            name='match.webp',
            payload=b'a' * 2048,
            mimetype='image/webp',
        )
        self._set_create_date(matching, old_enough)

        too_small = self._create_attachment(
            name='small.webp',
            payload=b'a' * 100,
            mimetype='image/webp',
        )
        self._set_create_date(too_small, old_enough)

        wrong_model = self._create_attachment(
            name='wrong-model.webp',
            payload=b'a' * 2048,
            mimetype='image/webp',
            res_model='res.users',
        )
        self._set_create_date(wrong_model, old_enough)

        too_new = self._create_attachment(
            name='new.webp',
            payload=b'a' * 2048,
            mimetype='image/webp',
        )

        wrong_mimetype = self._create_attachment(
            name='wrong-mime.png',
            payload=b'a' * 2048,
            mimetype='image/png',
        )
        self._set_create_date(wrong_mimetype, old_enough)

        found = self.env['ir.attachment'].search(
            rule._get_attachments_domain(['res.partner'])
        )

        self.assertEqual(found, matching)
        self.assertNotIn(too_small, found)
        self.assertNotIn(wrong_model, found)
        self.assertNotIn(too_new, found)
        self.assertNotIn(wrong_mimetype, found)

    def test_schedule_auto_compress_updates_datas_name_and_mimetype(self):
        self._create_rule()
        attachment = self._create_attachment(
            name='sample.png',
            payload=b'png-source',
            mimetype='image/png',
        )

        with patch(
            'odoo.addons.ir_attach_image_compressor.models.image_compression_rule.image_process',
            return_value=b'compressed-image',
        ) as image_process_mock:
            self.env['ir.image.compressor.rule']._schedule_auto_compress()

        attachment.invalidate_recordset(['datas', 'name', 'mimetype'])
        self.assertEqual(base64.b64decode(attachment.datas), b'compressed-image')
        self.assertEqual(attachment.name, 'sample.jpeg')
        self.assertEqual(attachment.mimetype, 'image/jpeg')
        image_process_mock.assert_called()

    def test_schedule_auto_compress_continues_after_processing_error(self):
        self._create_rule()
        failed = self._create_attachment(
            name='bad.png',
            payload=b'bad-image',
            mimetype='image/png',
        )
        succeeded = self._create_attachment(
            name='good.png',
            payload=b'good-image',
            mimetype='image/png',
        )

        def fake_image_process(payload, **kwargs):
            if payload == b'bad-image':
                raise ValueError('bad payload')
            return b'compressed-good-image'

        with patch(
            'odoo.addons.ir_attach_image_compressor.models.image_compression_rule.image_process',
            side_effect=fake_image_process,
        ):
            self.env['ir.image.compressor.rule']._schedule_auto_compress()

        failed.invalidate_recordset(['datas', 'name', 'mimetype'])
        succeeded.invalidate_recordset(['datas', 'name', 'mimetype'])

        self.assertEqual(base64.b64decode(failed.datas), b'bad-image')
        self.assertEqual(failed.name, 'bad.png')
        self.assertEqual(failed.mimetype, 'image/png')

        self.assertEqual(base64.b64decode(succeeded.datas), b'compressed-good-image')
        self.assertEqual(succeeded.name, 'good.jpeg')
        self.assertEqual(succeeded.mimetype, 'image/jpeg')
