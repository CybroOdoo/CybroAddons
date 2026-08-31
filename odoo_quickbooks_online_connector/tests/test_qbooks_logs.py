# -*- coding: utf-8 -*-

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestQbooksLogs(TransactionCase):

    def test_action_open_record_returns_target_action(self):
        partner = self.env['res.partner'].create({
            'name': 'QuickBooks Log Partner',
        })
        log = self.env['qbooks.logs'].create({
            'name': 'Import Partners',
            'operation_type': 'import',
            'res_model': 'res.partner',
            'res_id': partner.id,
            'status': 'success',
        })

        action = log.action_open_record()

        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'res.partner')
        self.assertEqual(action['res_id'], partner.id)
        self.assertEqual(action['view_mode'], 'form')
        self.assertEqual(action['target'], 'current')
