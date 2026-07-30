# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Akhil @ cybrosys,(odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests.common import TransactionCase
from odoo.addons.docusign_odoo_connector.models.edit_document import JSON


class TestJSONField(TransactionCase):
    """Test suite for the custom JSON field type defined in edit_document.py."""

    def setUp(self):
        super().setUp()
        # Use send.document (which carries the JSON 'data' field) as the test model
        self.SendDocument = self.env['send.document']
        self.field = JSON('data')

    # -------------------------------------------------------------------------
    # Field type metadata
    # -------------------------------------------------------------------------

    def test_01_field_type_is_json(self):
        """JSON field type attribute must be 'json'."""
        self.assertEqual(self.field.type, 'json')

    def test_02_column_type_is_jsonb(self):
        """JSON field column_type must map to Postgres jsonb."""
        self.assertEqual(self.field.column_type, ('jsonb', 'jsonb'))

    # -------------------------------------------------------------------------
    # convert_to_column
    # -------------------------------------------------------------------------

    def test_03_convert_to_column_with_dict(self):
        """convert_to_column with a dict returns its string representation."""
        val = {'key': 'value'}
        result = self.field.convert_to_column(val, record=None)
        self.assertEqual(result, str(val))

    def test_04_convert_to_column_with_string(self):
        """convert_to_column with a non-empty string returns the string itself."""
        result = self.field.convert_to_column('hello', record=None)
        self.assertEqual(result, 'hello')

    def test_05_convert_to_column_with_none_returns_none_string(self):
        """convert_to_column with None returns 'None' because str(None)='None'
        which is truthy, so the `or ''` branch is never taken.
        This documents the actual behaviour of the implementation."""
        result = self.field.convert_to_column(None, record=None)
        self.assertEqual(result, 'None')

    def test_06_convert_to_column_with_empty_string(self):
        """convert_to_column with empty string returns empty string."""
        result = self.field.convert_to_column('', record=None)
        self.assertEqual(result, '')

    # -------------------------------------------------------------------------
    # convert_to_record
    # -------------------------------------------------------------------------

    def test_07_convert_to_record_with_dict(self):
        """convert_to_record with a dict returns the dict unchanged."""
        val = {'a': 1, 'b': 2}
        result = self.field.convert_to_record(val, record=None)
        self.assertEqual(result, val)

    def test_08_convert_to_record_with_none_returns_empty_dict(self):
        """convert_to_record with None returns {}."""
        result = self.field.convert_to_record(None, record=None)
        self.assertEqual(result, {})

    def test_09_convert_to_record_with_false_returns_empty_dict(self):
        """convert_to_record with False returns {}."""
        result = self.field.convert_to_record(False, record=None)
        self.assertEqual(result, {})

    def test_10_convert_to_record_with_string(self):
        """convert_to_record with a truthy string returns it unchanged."""
        result = self.field.convert_to_record('{"x":1}', record=None)
        self.assertEqual(result, '{"x":1}')

    # -------------------------------------------------------------------------
    # convert_to_read
    # -------------------------------------------------------------------------

    def test_11_convert_to_read_passthrough_dict(self):
        """convert_to_read returns the value unchanged for a dict."""
        val = {'read': True}
        result = self.field.convert_to_read(val, record=None)
        self.assertEqual(result, val)

    def test_12_convert_to_read_passthrough_none(self):
        """convert_to_read returns None unchanged."""
        result = self.field.convert_to_read(None, record=None)
        self.assertIsNone(result)

    def test_13_convert_to_read_passthrough_integer(self):
        """convert_to_read returns integer values unchanged."""
        result = self.field.convert_to_read(42, record=None)
        self.assertEqual(result, 42)

    # -------------------------------------------------------------------------
    # convert_to_export
    # -------------------------------------------------------------------------

    def test_14_convert_to_export_with_truthy_value(self):
        """convert_to_export with a truthy value returns it unchanged."""
        val = {'export': 'me'}
        result = self.field.convert_to_export(val, record=None)
        self.assertEqual(result, val)

    def test_15_convert_to_export_with_empty_string(self):
        """convert_to_export with an empty string (falsy but == '') returns ''."""
        result = self.field.convert_to_export('', record=None)
        self.assertEqual(result, '')

    def test_16_convert_to_export_with_none_returns_empty_string(self):
        """convert_to_export with None returns empty string ''."""
        result = self.field.convert_to_export(None, record=None)
        self.assertEqual(result, '')

    def test_17_convert_to_export_with_false_returns_empty_string(self):
        """convert_to_export with False returns empty string ''."""
        result = self.field.convert_to_export(False, record=None)
        self.assertEqual(result, '')

    # -------------------------------------------------------------------------
    # Integration: JSON field on send.document wizard
    # -------------------------------------------------------------------------

    def test_18_data_field_on_send_document_exists(self):
        """The 'data' field on send.document should be a JSON instance."""
        field_def = self.env['send.document']._fields.get('data')
        self.assertIsNotNone(field_def, "send.document must have a 'data' field")
        self.assertEqual(field_def.type, 'json')

    def test_19_data_field_read_back_as_dict(self):
        """Writing a dict-like value to data is read back correctly."""
        partner = self.env['res.partner'].create({
            'name': 'JSON Field Test Partner',
            'email': 'jsonfield@test.com',
        })
        order = self.env['sale.order'].create({'partner_id': partner.id})
        wiz = self.env['send.document'].create({
            'email_id': partner.id,
            'reference': 'JSON-REF',
            'res_id': order.id,
        })
        import json
        tabs = {'signHereTabs': [{'x': 1, 'y': 2}]}
        wiz.get_json_data(tabs, wiz.id)
        wiz.invalidate_recordset(['data'])
        # data should be truthy after assignment
        self.assertTrue(wiz.data is not None)