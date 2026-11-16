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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestTextCommander(TransactionCase):
    """Test suite for Text Commander module functionality and coverage."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ir_model = cls.env['ir.model']

        # Ensure a known country exists for translated name testing
        cls.country = cls.env['res.country'].search(
            [('code', '=', 'BE')], limit=1,
        )
        if not cls.country:
            cls.country = cls.env['res.country'].create({
                'name': 'Belgium',
                'code': 'BE',
            })

        # Create parent company and child contact for relational testing
        cls.company_partner = cls.env['res.partner'].create({
            'name': 'Text Commander Test Company Alpha',
            'is_company': True,
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Text Commander Test Contact Alpha',
            'email': 'commander_test_alpha@example.com',
            'type': 'contact',
            'parent_id': cls.company_partner.id,
            'country_id': cls.country.id,
        })

    def test_01_check_model_existing(self):
        """Test check_model with an existing model name."""
        result = self.ir_model.check_model('Contact')
        self.assertTrue(result, "check_model should return a match for 'Contact'")
        self.assertEqual(result[0].get('model'), 'res.partner')

    def test_02_check_model_case_insensitive(self):
        """Test check_model case insensitivity."""
        result = self.ir_model.check_model('contact')
        self.assertTrue(result, "check_model should be case-insensitive")
        self.assertEqual(result[0].get('model'), 'res.partner')

    def test_03_check_model_not_found(self):
        """Test check_model with non-existent model name."""
        result = self.ir_model.check_model('non_existent_model_xyz_999')
        self.assertFalse(result)

    def test_04_get_records_regex_1_translated(self):
        """Test get_records with regex=1 on translated name (res.country)."""
        data = {
            'model': 'res.country',
            'record': self.country.name.lower(),
            'regex': 1,
        }
        record_ids = self.ir_model.get_records(data)
        self.assertIn(self.country.id, record_ids)

    def test_05_get_records_regex_1_non_translated(self):
        """Test get_records with regex=1 on non-translated name (res.partner)."""
        data = {
            'model': 'res.partner',
            'record': 'commander test contact alpha',
            'regex': 1,
        }
        record_ids = self.ir_model.get_records(data)
        self.assertIn(self.partner.id, record_ids)

    def test_06_get_records_regex_2_many2one(self):
        """Test get_records with regex=2 and many2one field type."""
        data = {
            'model': 'res.partner',
            'field': 'parent_id',
            'field_type': 'many2one',
            'field_relation': 'res.partner',
            'field_string': f" {self.company_partner.name}",
            'regex': 2,
        }
        record_ids = self.ir_model.get_records(data)
        self.assertIn(self.partner.id, record_ids)

    def test_07_get_records_regex_2_selection(self):
        """Test get_records with regex=2 and selection field type."""
        data = {
            'model': 'res.partner',
            'field': 'type',
            'field_type': 'selection',
            'field_string': ' Contact',
            'regex': 2,
        }
        record_ids = self.ir_model.get_records(data)
        self.assertIn(self.partner.id, record_ids)

    def test_08_get_records_regex_2_other_field(self):
        """Test get_records with regex=2 and char field type."""
        data = {
            'model': 'res.partner',
            'field': 'email',
            'field_type': 'char',
            'field_string': ' commander_test_alpha@example.com',
            'regex': 2,
        }
        record_ids = self.ir_model.get_records(data)
        self.assertIn(self.partner.id, record_ids)

    def test_09_get_selection_values(self):
        """Test _get_selection_values helper method."""
        data = {
            'model': 'res.partner',
            'field': 'type',
        }
        selection_values = self.ir_model._get_selection_values(data)
        self.assertTrue(selection_values)
        keys = [item[0] for item in selection_values]
        self.assertIn('contact', keys)

    def test_10_check_fields_model_single_word(self):
        """Test check_fields_model with a single-word field description."""
        data = {
            'model': 'res.partner',
            'field_string': ['Email'],
        }
        result = self.ir_model.check_fields_model(data)
        self.assertTrue(result)
        self.assertEqual(result[0].get('name'), 'email')
        self.assertEqual(result[0].get('del'), 'Email')

    def test_11_check_fields_model_multi_word(self):
        """Test check_fields_model with a multi-word field description."""
        data = {
            'model': 'res.partner',
            'field_string': ['Related', 'Company'],
        }
        result = self.ir_model.check_fields_model(data)
        self.assertTrue(result)
        self.assertEqual(result[0].get('name'), 'parent_id')
        self.assertEqual(result[0].get('del'), 'Related Company')
        self.assertTrue(result[0].get('relation'))

    def test_12_check_fields_model_not_found(self):
        """Test check_fields_model when no field matches description."""
        data = {
            'model': 'res.partner',
            'field_string': ['Unknown', 'NonExistent', 'Field'],
        }
        result = self.ir_model.check_fields_model(data)
        self.assertEqual(result, [])

    def test_13_check_model_technical_name(self):
        """Test check_model with technical model name like 'res.partner'."""
        result = self.ir_model.check_model('res.partner')
        self.assertTrue(result)
        self.assertEqual(result[0].get('model'), 'res.partner')

    def test_14_check_fields_model_technical_name(self):
        """Test check_fields_model with technical field name."""
        data = {
            'model': 'res.partner',
            'field_string': ['email'],
        }
        result = self.ir_model.check_fields_model(data)
        self.assertTrue(result)
        self.assertEqual(result[0].get('name'), 'email')

    def test_15_get_records_regex_2_parent_partner(self):
        """Test get_records locating child through parent company name."""
        data = {
            'model': 'res.partner',
            'field': 'parent_id',
            'field_type': 'many2one',
            'field_relation': 'res.partner',
            'field_string': 'Text Commander Test Company Alpha',
            'regex': 2,
        }
        record_ids = self.ir_model.get_records(data)
        self.assertIn(self.partner.id, record_ids)

    def test_16_get_records_partial_match(self):
        """Test get_records with partial query string."""
        data = {
            'model': 'res.partner',
            'field': 'parent_id',
            'field_type': 'many2one',
            'field_relation': 'res.partner',
            'field_string': 'Test Company Al',
            'regex': 2,
        }
        record_ids = self.ir_model.get_records(data)
        self.assertIn(self.partner.id, record_ids)

    def test_17_get_records_auto_resolves_relation(self):
        """Test get_records auto-discovers relation if missing in payload."""
        data = {
            'model': 'res.partner',
            'field': 'parent_id',
            'field_type': 'many2one',
            'field_string': 'Test Company Alpha',
            'regex': 2,
        }
        record_ids = self.ir_model.get_records(data)
        self.assertIn(self.partner.id, record_ids)

    def test_18_check_model_empty_string(self):
        """Test check_model with empty or whitespace input."""
        self.assertEqual(self.ir_model.check_model(''), [])
        self.assertEqual(self.ir_model.check_model(None), [])

    def test_19_get_records_invalid_model(self):
        """Test get_records returns [] for non-existent model."""
        data = {
            'model': 'does.not.exist',
            'record': 'anything',
            'regex': 1,
        }
        self.assertEqual(self.ir_model.get_records(data), [])
