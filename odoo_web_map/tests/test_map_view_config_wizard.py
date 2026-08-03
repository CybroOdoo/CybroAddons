# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

class TestMapViewConfigWizard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestMapViewConfigWizard, cls).setUpClass()
        
        # We find a model ID for testing configurations
        cls.partner_model = cls.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)

    def test_get_partner_field_selection(self):
        """Test selection getter provides mapped fields arrays"""
        wizard = self.env['map.view.config.wizard'].new({
            'model_id': self.partner_model.id
        })
        selections = wizard._get_partner_field_selection()
        
        self.assertIsInstance(selections, list)
        if selections: # assuming res partner has partner fields
            self.assertEqual(len(selections[0]), 2)
            
    def test_build_map_view_arch_string(self):
        """Test architecture xml builder"""
        wizard = self.env['map.view.config.wizard'].new({
            'model_id': self.partner_model.id,
            'partner_field_id': 'id'
        })
        xml = wizard._build_map_view_arch()
        self.assertIn('<map>', xml)
        self.assertIn('<field name="display_name"/>', xml)
