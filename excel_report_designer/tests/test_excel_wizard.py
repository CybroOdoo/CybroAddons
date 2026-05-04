# -*- coding: utf-8 -*-

from odoo.tests import common
import json

class TestExcelWizard(common.TransactionCase):

    def setUp(self):
        super(TestExcelWizard, self).setUp()
        self.model_res_partner = self.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        self.field_name = self.env['ir.model.fields'].search([('model_id', '=', self.model_res_partner.id), ('name', '=', 'name')], limit=1)
        
        self.report = self.env['report.excel'].create({
            'name': 'Partner Test Report',
            'model_id': self.model_res_partner.id,
            'fields_ids': [(6, 0, [self.field_name.id])],
            'binding_type': 'action',
        })
        
        self.partner = self.env['res.partner'].create({'name': 'Wizard Test Partner'})

    def test_01_wizard_print(self):
        """Test the wizard print action"""
        wizard = self.env['excel.report.wizards'].with_context(
            excel=self.report.id,
            active_ids=[self.partner.id],
            active_model='res.partner'
        ).create({})
        
        action = wizard.print_excel_report()
        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertEqual(action['report_type'], 'xlsx')
        
        options = json.loads(action['data']['options'])
        self.assertEqual(options['report_name'], self.report.name)
        self.assertIn(self.partner.id, options['active_model_id'])
