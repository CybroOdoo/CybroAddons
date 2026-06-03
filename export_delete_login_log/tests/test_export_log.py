# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestExportLog(TransactionCase):
    """Tests for export log creation."""

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Export Partner',
            'email': 'export@example.com',
        })
        self.partner_model = self.env['ir.model'].sudo().search(
            [('model', '=', 'res.partner')],
            limit=1,
        )

    def test_action_create_export_log_creates_log_with_fields(self):
        self.env['export.log'].action_create_export_log({
            'records': [{
                'rec_id': self.partner.id,
                'rec_model': 'res.partner',
            }],
            'exportList': [
                {'field_name': 'name'},
                {'field_name': 'email'},
            ],
        })

        log = self.env['export.log'].sudo().search(
            [('rec_id', '=', str(self.partner.id))],
            limit=1,
        )
        self.assertTrue(log)
        self.assertEqual(log.rec_model_id, self.partner_model)
        self.assertEqual(log.rec_name, 'Export Partner')
        self.assertEqual(
            set(log.exported_fields_ids.mapped('name')),
            {'name', 'email'},
        )
        self.assertEqual(log.export_user_id, self.env.user)
