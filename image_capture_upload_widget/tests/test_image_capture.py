# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestImageCapture(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.image_capture = cls.env['image.capture']

    def test_action_save_image_png_data_url(self):
        image_data = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB'
        data_url = f'data:image/png;base64,{image_data}'

        result = self.image_capture.action_save_image(data_url)

        self.assertEqual(result, image_data)

    def test_action_save_image_jpeg_data_url(self):
        image_data = '/9j/4AAQSkZJRgABAQAAAQABAAD'
        data_url = f'data:image/jpeg;base64,{image_data}'

        result = self.image_capture.action_save_image(data_url)

        self.assertEqual(result, image_data)

    def test_action_save_image_empty_payload(self):
        result = self.image_capture.action_save_image(
            'data:image/png;base64,'
        )

        self.assertEqual(result, '')
