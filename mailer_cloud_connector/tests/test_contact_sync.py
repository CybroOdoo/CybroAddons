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
#############################################################################
from odoo.tests.common import TransactionCase

class TestContactSync(TransactionCase):

    def test_dynamic_selection(self):
        """Test the dynamic selection of Odoo fields in contact.sync."""
        ContactSync = self.env['contact.sync']
        selection = ContactSync.dynamic_selection()
        self.assertTrue(isinstance(selection, list))
        field_names = [s[0] for s in selection]
        self.assertIn('name', field_names)
        self.assertIn('email', field_names)

    def test_contact_sync_create_and_read(self):
        """Test creating and reading a contact.sync record."""
        sync_record = self.env['mailer.cloud.api.sync'].create({
            'api_key': 'key_123',
            'name': 'Sync Instance',
        })
        prop = self.env['mailer.cloud.properties'].create({
            'name': 'Phone Property',
            'type': 'text',
            'authorization_id': sync_record.id,
        })
        mapping = self.env['contact.sync'].create({
            'property_id': prop.id,
            'contact_fields': 'phone',
            'sync_id': sync_record.id,
        })
        self.assertEqual(mapping.property_id, prop)
        self.assertEqual(mapping.contact_fields, 'phone')
        self.assertEqual(mapping.sync_id, sync_record)
        self.assertIn(mapping, sync_record.contact_mapping_ids)
