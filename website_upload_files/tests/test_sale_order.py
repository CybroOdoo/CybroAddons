# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################

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
            'raw': b'test attachment content',
        })

    def test_compute_attachment_count(self):
        self.assertEqual(self.sale_order.attachment_count, 0)

        self._create_attachment('first.txt')
        self._create_attachment('second.txt')
        self.sale_order.invalidate_recordset(['attachment_count'])

        self.assertEqual(self.sale_order.attachment_count, 2)

    def test_compute_attachment_count_several_orders(self):
        other = self.env['sale.order'].create({'partner_id': self.partner.id})
        self._create_attachment('first.txt')
        orders = self.sale_order | other
        orders.invalidate_recordset(['attachment_count'])
        self.assertEqual(orders.mapped('attachment_count'), [1, 0])

    def test_action_show_attachments_one_order(self):
        other = self.env['sale.order'].create({'partner_id': self.partner.id})
        with self.assertRaises(ValueError):
            (self.sale_order | other).action_show_attachments()

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
