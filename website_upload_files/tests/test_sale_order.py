import base64

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSaleOrderAttachments(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Attachment Count Customer',
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
        })

    def _create_attachment(self, name):
        return self.env['ir.attachment'].create({
            'name': name,
            'res_name': name,
            'type': 'binary',
            'res_model': 'sale.order',
            'res_id': self.sale_order.id,
            'datas': base64.b64encode(b'test attachment content'),
        })

    def test_compute_attachment_count(self):
        self.assertEqual(self.sale_order.attachment_count, 0)

        self._create_attachment('first.txt')
        self._create_attachment('second.txt')
        self.sale_order.invalidate_recordset(['attachment_count'])

        self.assertEqual(self.sale_order.attachment_count, 2)

    def test_action_show_attachments(self):
        action = self.sale_order.action_show_attachments()

        self.assertEqual(action['name'], 'Attachments')
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'ir.attachment')
        self.assertEqual(action['view_mode'], 'kanban,form')
        self.assertEqual(action['domain'], [
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', self.sale_order.id),
        ])
