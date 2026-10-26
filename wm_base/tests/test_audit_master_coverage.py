from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'wm_base')
class TestAuditMasterCoverage(TransactionCase):
    """Audit mixin internals, immutable logs and master-data helpers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env['ir.config_parameter'].sudo().set_param('wm_base.group_wm_audit_trail', 'True')
        cls.Category = cls.env['wm.waste.category']

    def test_get_audit_value_types(self):
        cat = self.Category.create({'name': 'AV Cat', 'code': 'AVC'})
        get = cat._get_audit_value
        self.assertEqual(get('name', False), '')
        self.assertEqual(get('name', None), '')
        self.assertEqual(get('name', 'x' * 300), 'x' * 197 + '...')
        self.assertEqual(get('active', True), 'Yes')
        self.assertEqual(get('active', False), '')
        self.assertEqual(get('default_processing', 'recycle'), 'Recycle')
        self.assertEqual(get('company_id', self.env.company.id), self.env.company.display_name)
        self.assertEqual(get('company_id', self.env.company), self.env.company.display_name)
        self.assertEqual(get('company_id', 999999999), 'Deleted (999999999)')
        self.assertEqual(get('material_ids', {1, 2}), '2 record(s)')
        self.assertEqual(get('unknown_field', 5), '5')
        self.assertEqual(get('unknown_field', 'y' * 300), 'y' * 197 + '...')

    def test_get_audit_value_binary_and_html(self):
        cat = self.Category.create({'name': 'Bin Cat', 'code': 'BIN'})
        fake = {'fake_bin': fields.Binary(), 'fake_html': fields.Html()}
        with patch.object(type(cat), '_fields', {**cat._fields, **fake}):
            self.assertEqual(cat._get_audit_value('fake_bin', b'a' * 2048), '[Binary File: 2.0 KB]')
            self.assertEqual(cat._get_audit_value('fake_bin', 'a' * 1024), '[Binary File: 0.8 KB]')
            self.assertEqual(cat._get_audit_value('fake_html', '<p>Hello   world</p>'), 'Hello world')
            self.assertEqual(len(cat._get_audit_value('fake_html', '<p>%s</p>' % ('w' * 400))), 200)

    def test_create_write_unlink_logged(self):
        Log = self.env['wm.audit.log']
        model = self.env['ir.model']._get('wm.waste.category')
        cat = self.Category.create({'name': 'Aud One', 'code': 'AUD1'})
        logs = Log.search([('model_id', '=', model.id), ('res_id', '=', cat.id)])
        self.assertEqual(logs.mapped('action'), ['create'])
        self.assertEqual(logs.new_value, 'Aud One')
        cat.write({'name': 'Aud Two'})
        w = Log.search([('model_id', '=', model.id), ('res_id', '=', cat.id), ('action', '=', 'write')])
        self.assertEqual((w.old_value, w.new_value), ('Aud One', 'Aud Two'))
        self.assertEqual(w.user_id, self.env.user)
        # unchanged value is not logged
        cat.write({'name': 'Aud Two'})
        self.assertEqual(Log.search_count([('res_id', '=', cat.id), ('model_id', '=', model.id),
                                           ('action', '=', 'write')]), 1)
        # non-audited field is not logged
        cat.write({'sequence': 77})
        self.assertEqual(Log.search_count([('res_id', '=', cat.id), ('model_id', '=', model.id),
                                           ('action', '=', 'write')]), 1)
        cid = cat.id
        cat.unlink()
        d = Log.search([('model_id', '=', model.id), ('res_id', '=', cid), ('action', '=', 'unlink')])
        self.assertEqual(d.new_value, '[Deleted]')
        self.assertEqual(d.old_value, 'Aud Two')

    def test_log_status_transition(self):
        cat = self.Category.create({'name': 'Trans Cat', 'code': 'TRC'})
        self.assertTrue(cat.log_status_transition('A', 'B', reason='because'))
        t = self.env['wm.status.transition.log'].search([('res_id', '=', cat.id)])
        self.assertEqual((t.old_state, t.new_state, t.reason), ('A', 'B', 'because'))
        self.assertEqual(t.record_name, cat.display_name)
        cat.log_status_transition('B', 'C')
        self.assertIn('Manual State Change', self.env['wm.status.transition.log'].search(
            [('res_id', '=', cat.id)]).mapped('reason'))
        self.env['ir.config_parameter'].sudo().set_param('wm_base.group_wm_audit_trail', 'False')
        self.assertFalse(cat.log_status_transition('C', 'D'))

    def test_logs_are_immutable_and_record_name(self):
        cat = self.Category.create({'name': 'Imm Cat', 'code': 'IMC'})
        model = self.env['ir.model']._get('wm.waste.category')
        log = self.env['wm.audit.log'].search([('res_id', '=', cat.id), ('model_id', '=', model.id)])
        self.assertEqual(log.record_name, cat.display_name)
        with self.assertRaises(UserError):
            log.write({'new_value': 'x'})
        with self.assertRaises(UserError):
            log.unlink()
        cat.log_status_transition('A', 'B')
        t = self.env['wm.status.transition.log'].search([('res_id', '=', cat.id)])
        with self.assertRaises(UserError):
            t.write({'reason': 'x'})
        with self.assertRaises(UserError):
            t.unlink()
        # deleted target and unknown record names
        ghost = self.env['wm.audit.log'].create({
            'model_id': model.id, 'res_id': 999999999, 'action': 'write'})
        self.assertIn('[Deleted]', ghost.record_name)

    def test_container_type_compatible_categories(self):
        c1 = self.Category.create({'name': 'CT Cat 1', 'code': 'CT1'})
        c2 = self.Category.create({'name': 'CT Cat 2', 'code': 'CT2'})
        ct = self.env['wm.container.type'].create({'name': 'Bin', 'category_ids': [(6, 0, c1.ids)]})
        self.assertEqual(ct.compatible_category_ids, c1)
        ct.compatible_category_ids = c2
        self.assertEqual(ct.category_ids, c2)
        # capacity mirrors capacity_volume
        ct.capacity_volume = 120.0
        self.assertEqual(ct.capacity, 120.0)
        ct.capacity = 240.0
        self.assertEqual(ct.capacity_volume, 240.0)

    def test_res_partner_generator_default(self):
        partner = self.env['res.partner'].create({'name': 'Gen Partner'})
        self.assertFalse(partner.is_generator)
        partner.is_generator = True
        self.assertTrue(partner.is_generator)

    def test_billing_rule_defaults_and_cascade(self):
        cat = self.Category.create({'name': 'Bill Cat', 'code': 'BLC'})
        rule = self.env['wm.category.billing.rule'].create({'category_id': cat.id, 'price': 2.5})
        self.assertEqual(rule.billing_basis, 'per_kg')
        cat.with_context(audit_skip=True).unlink()
        self.assertFalse(rule.exists())
