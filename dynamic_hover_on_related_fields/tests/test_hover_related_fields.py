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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import base64
from types import SimpleNamespace

from psycopg2 import IntegrityError

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestHoverRelatedFields(TransactionCase):
    """Tests for the hover related fields configuration and tooltip data."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.hover_model = cls.env['hover.related.fields']
        cls.partner_model = cls.env['ir.model']._get('res.partner')
        cls.fields_model = cls.env['ir.model.fields']
        cls.name_field = cls.fields_model._get('res.partner', 'name')
        cls.email_field = cls.fields_model._get('res.partner', 'email')
        cls.parent_field = cls.fields_model._get('res.partner', 'parent_id')
        cls.parent = cls.env['res.partner'].create({
            'name': 'Hover Parent',
            'email': 'parent@example.com',
        })
        cls.child = cls.env['res.partner'].create({
            'name': 'Hover Child',
            'parent_id': cls.parent.id,
        })

    def _create_config(self, fields_list):
        return self.hover_model.create({
            'model_id': self.partner_model.id,
            'field_ids': [(6, 0, [f.id for f in fields_list])],
        })

    def test_default_values_and_display_name(self):
        config = self._create_config([self.name_field])
        self.assertTrue(config.active)
        self.assertEqual(config.display_name, self.partner_model.name)

    def test_unique_model_configuration(self):
        self._create_config([self.name_field])
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'):
            with self.cr.savepoint():
                self._create_config([self.email_field])

    def test_compute_model_ids(self):
        config = self._create_config([self.name_field])
        self.assertIn(self.partner_model, config.model_ids)
        new_config = self.hover_model.new({})
        self.assertIn(self.partner_model.id, new_config.model_ids.ids)

    def test_tooltip_many2one_data(self):
        self._create_config([self.name_field, self.email_field])
        data = self.hover_model.finding_the_data_to_show_tooltip({
            'resModel': 'res.partner',
            'resId': self.child.id,
            'field': {'name': 'parent_id', 'relation': 'res.partner'},
        })
        values = {line['field_name']: line['value'] for line in data}
        self.assertEqual(values['name'], 'Hover Parent')
        self.assertEqual(values['email'], 'parent@example.com')
        self.assertEqual({line['ttype'] for line in data}, {'char'})

    def test_tooltip_without_configuration(self):
        data = self.hover_model.finding_the_data_to_show_tooltip({
            'resModel': 'res.partner',
            'resId': self.child.id,
            'field': {'name': 'parent_id', 'relation': 'res.partner'},
        })
        self.assertEqual(data, [])

    def test_tooltip_related_record_data(self):
        self._create_config([self.name_field, self.parent_field])
        data = self.hover_model.finding_the_data_to_show_tooltip_many2many({
            'viewMode': 'form',
            'related_record_id': self.child.id,
            'field': {'name': 'parent_id', 'relation': 'res.partner'},
        })
        values = {line['field_name']: line['value'] for line in data}
        self.assertEqual(values['name'], 'Hover Child')
        self.assertEqual(values['parent_id'], 'Hover Parent')

    def test_tooltip_binary_value(self):
        raw = b'binary-content'
        field = SimpleNamespace(name='image_1920', ttype='binary')
        value = self.hover_model._get_tooltip_value(
            {'image_1920': raw}, field)
        self.assertEqual(value, base64.b64encode(raw).decode('utf-8'))
        empty = self.hover_model._get_tooltip_value(
            {'image_1920': False}, field)
        self.assertFalse(empty)

    def test_tooltip_list_mode_fallback(self):
        data = self.hover_model.finding_the_data_to_show_tooltip_many2many({
            'viewMode': 'list',
            'related_record_id': self.parent.id,
            'field': {'name': 'parent_id', 'relation': 'res.partner'},
        })
        self.assertEqual(data, 'Hover Parent')
        form_data = self.hover_model.finding_the_data_to_show_tooltip_many2many({
            'viewMode': 'form',
            'related_record_id': self.parent.id,
            'field': {'name': 'parent_id', 'relation': 'res.partner'},
        })
        self.assertEqual(form_data, [])
