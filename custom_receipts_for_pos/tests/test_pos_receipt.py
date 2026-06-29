# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPosReceipt(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestPosReceipt, cls).setUpClass()
        # Create a pos.receipt record with custom design
        cls.pos_receipt = cls.env['pos.receipt'].create({
            'name': 'Test Receipt',
            'design_receipt': '<receipt>Test Design</receipt>',
        })

    # -------------------------------------------------------------------------
    # pos.receipt model tests
    # -------------------------------------------------------------------------

    def test_pos_receipt_creation(self):
        """Test that pos.receipt records are created with correct field values."""
        self.assertEqual(self.pos_receipt.name, 'Test Receipt')
        self.assertEqual(self.pos_receipt.design_receipt, '<receipt>Test Design</receipt>')

    def test_pos_receipt_load_data_fields(self):
        """Test that _load_pos_data_fields returns the expected field list."""
        pos_config = self.env['pos.config'].search([], limit=1)
        fields = self.env['pos.receipt']._load_pos_data_fields(pos_config)
        self.assertIn('id', fields)
        self.assertIn('name', fields)
        self.assertIn('design_receipt', fields)

    def test_pos_receipt_search_read_via_mixin(self):
        """Test that pos.receipt records are searchable via search_read."""
        receipts = self.env['pos.receipt'].search_read(
            domain=[('name', '=', 'Test Receipt')],
            fields=['name', 'design_receipt'],
        )
        self.assertTrue(len(receipts) > 0,
                        "Should find at least one matching receipt.")
        found = next((r for r in receipts if r['id'] == self.pos_receipt.id), None)
        self.assertIsNotNone(found, "Our test receipt should be in the results.")
        self.assertEqual(found['design_receipt'], '<receipt>Test Design</receipt>')

    # -------------------------------------------------------------------------
    # pos.config model tests
    # -------------------------------------------------------------------------

    def test_pos_config_custom_receipt_fields(self):
        """Test pos.config custom fields: is_custom_receipt and receipt_design_id."""
        pos_config = self.env['pos.config'].search([], limit=1)
        if not pos_config:
            self.skipTest("No pos.config found in DB, skipping.")

        # Assign a receipt design to the config
        pos_config.write({
            'receipt_design_id': self.pos_receipt.id,
            'is_custom_receipt': True,
        })

        self.assertEqual(pos_config.receipt_design_id.id, self.pos_receipt.id)
        self.assertTrue(pos_config.is_custom_receipt)
        # Validate the related field resolves correctly on a real DB record
        self.assertEqual(pos_config.design_receipt, '<receipt>Test Design</receipt>')

    # -------------------------------------------------------------------------
    # pos.session model tests
    # -------------------------------------------------------------------------

    def test_pos_session_load_models_includes_pos_receipt(self):
        """Test that _load_pos_data_models includes pos.receipt in the data list."""
        pos_config = self.env['pos.config'].search([], limit=1)
        if not pos_config:
            self.skipTest("No pos.config found in DB, skipping.")

        session_model = self.env['pos.session']
        models_list = session_model._load_pos_data_models(pos_config)
        self.assertIn('pos.receipt', models_list,
                      "pos.receipt should be included in the POS UI data models.")
