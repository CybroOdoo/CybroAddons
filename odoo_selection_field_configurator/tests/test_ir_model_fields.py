# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestIrModelFields(TransactionCase):
    """Tests for monkey-patched ir.model.fields methods."""

    def setUp(self):
        super(TestIrModelFields, self).setUp()
        self.IrModelFields = self.env['ir.model.fields']
        self.IrModelFieldsSelection = self.env['ir.model.fields.selection']

        # Get a base selection field to test on, e.g., 'type' on 'res.partner'
        self.field_type = self.IrModelFields.search([
            ('model', '=', 'res.partner'),
            ('name', '=', 'type')
        ], limit=1)

    def test_create_selection_field(self):
        """Test creating a selection value for a base field does not raise an error."""
        selection = self.IrModelFieldsSelection.create({
            'field_id': self.field_type.id,
            'value': 'test_custom_type',
            'name': 'Test Custom Type',
            'sequence': 100,
        })
        self.assertTrue(selection.id)
        self.assertEqual(selection.value, 'test_custom_type')

    def test_write_selection_field(self):
        """Test writing to a selection value for a base field does not raise an error."""
        selection = self.IrModelFieldsSelection.create({
            'field_id': self.field_type.id,
            'value': 'test_custom_type2',
            'name': 'Test Custom Type 2',
            'sequence': 100,
        })
        selection.write({'name': 'Updated Custom Type 2'})
        self.assertEqual(selection.name, 'Updated Custom Type 2')

    def test_unlink_selection_field(self):
        """Test unlinking a selection value does not raise an error."""
        selection = self.IrModelFieldsSelection.create({
            'field_id': self.field_type.id,
            'value': 'test_custom_type3',
            'name': 'Test Custom Type 3',
            'sequence': 100,
        })
        # Should not raise UserError on unlink due to monkey patch
        selection.unlink()
        self.assertFalse(selection.exists())

    def test_description_selection(self):
        """Test custom selections are included in _description_selection."""
        self.IrModelFieldsSelection.create({
            'field_id': self.field_type.id,
            'value': 'test_custom_type4',
            'name': 'Test Custom Type 4',
            'sequence': 100,
        })
        # Call fields_get to trigger _description_selection
        fields_info = self.env['res.partner'].fields_get(['type'])
        selections = dict(fields_info['type']['selection'])
        self.assertIn('test_custom_type4', selections)
        self.assertEqual(selections['test_custom_type4'], 'Test Custom Type 4')
