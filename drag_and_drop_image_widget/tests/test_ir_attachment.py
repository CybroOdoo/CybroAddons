# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestIrAttachment(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Attachment = cls.env['ir.attachment']

    def _call_save_image(self, record, field_name, url):
        return self.Attachment.action_save_drag_and_drop_image(
            {
                'resModel': record._name,
                'id': record.id,
                'name': field_name,
            },
            url,
        )

    def _create_target_attachment(self, datas=False):
        return self.Attachment.create({
            'name': 'Image Drop Target',
            'type': 'binary',
            'datas': datas,
        })

    def test_action_save_drag_and_drop_image_writes_base64_payload(self):
        attachment = self._create_target_attachment()
        image_payload = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB'
        url = 'data:image/png;base64,%s' % image_payload

        result = self._call_save_image(attachment, 'datas', url)

        attachment.invalidate_recordset(['datas'])
        self.assertTrue(result)
        self.assertEqual(attachment.datas.decode(), image_payload)

    def test_action_save_drag_and_drop_image_replaces_existing_image(self):
        attachment = self._create_target_attachment(
            'b2xkLWltYWdlLXBheWxvYWQ=')
        image_payload = 'bmV3LWltYWdlLXBheWxvYWQ='

        result = self._call_save_image(
            attachment,
            'datas',
            'data:image/jpeg;base64,%s' % image_payload,
        )

        attachment.invalidate_recordset(['datas'])
        self.assertTrue(result)
        self.assertEqual(attachment.datas.decode(), image_payload)

    def test_action_save_drag_and_drop_image_requires_data_url_payload(self):
        attachment = self._create_target_attachment()

        with self.assertRaises(IndexError):
            self._call_save_image(attachment, 'datas', 'missing-comma')

        attachment.invalidate_recordset(['datas'])
        self.assertFalse(attachment.datas)
