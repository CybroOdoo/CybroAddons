# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestDeleteLog(TransactionCase):
    """Tests for delete log tracking."""

    def setUp(self):
        super().setUp()
        self.config_parameter = self.env['ir.config_parameter'].sudo()
        self.partner_model = self.env['ir.model'].sudo().search(
            [('model', '=', 'res.partner')],
            limit=1,
        )

    def test_unlink_creates_delete_log_for_tracked_model(self):
        partner = self.env['res.partner'].create({
            'name': 'Tracked Delete Partner',
        })
        self.config_parameter.set_param(
            'export_delete_login_log.delete_log_models_ids',
            [self.partner_model.id],
        )

        partner.unlink()

        log = self.env['delete.log'].sudo().search(
            [('rec_id', '=', str(partner.id))],
            limit=1,
        )
        self.assertTrue(log)
        self.assertEqual(log.rec_model_id, self.partner_model)
        self.assertEqual(log.rec_name, 'Tracked Delete Partner')
        self.assertEqual(log.user_id, self.env.user)

    def test_unlink_does_not_create_delete_log_for_untracked_model(self):
        partner = self.env['res.partner'].create({
            'name': 'Untracked Delete Partner',
        })
        self.config_parameter.set_param(
            'export_delete_login_log.delete_log_models_ids',
            [],
        )

        partner.unlink()

        log = self.env['delete.log'].sudo().search(
            [('rec_id', '=', str(partner.id))],
            limit=1,
        )
        self.assertFalse(log)
