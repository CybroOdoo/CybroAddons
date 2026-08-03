# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

class TestMediaTag(TransactionCase):

    def setUp(self):
        super(TestMediaTag, self).setUp()
        self.MediaTag = self.env['media.tag']

    def test_create_tag(self):
        """Test creating a media tag."""
        tag = self.MediaTag.create({'name': 'Test Tag'})
        self.assertEqual(tag.name, 'Test Tag')
