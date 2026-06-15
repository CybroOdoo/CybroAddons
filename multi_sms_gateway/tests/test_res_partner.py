# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestResPartner(TransactionCase):

    def test_send_sms_returns_wizard_action_with_selected_partner_mobiles(self):
        partners = self.env['res.partner'].create([
            {
                'name': 'SMS Partner One',
                'mobile': '+15550000001',
            },
            {
                'name': 'SMS Partner Two',
                'mobile': '+15550000002',
            },
        ])

        action = partners[0].with_context(active_ids=partners.ids).send_sms()

        self.assertEqual(action['name'], 'Send SMS')
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'send.sms')
        self.assertEqual(action['view_mode'], 'form')
        self.assertEqual(action['target'], 'new')
        self.assertEqual(
            action['context']['default_sms_to'],
            '+15550000001,+15550000002',
        )

    def test_send_sms_handles_empty_active_ids(self):
        partner = self.env['res.partner'].create({'name': 'No Active IDs'})

        action = partner.with_context(active_ids=[]).send_sms()

        self.assertEqual(action['context']['default_sms_to'], '')
