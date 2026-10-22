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
import base64

from lxml import etree

from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSaleOrderAttachment(TransactionCase):
    """Tests for the attachments field on sale orders."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Customer'})
        cls.order = cls.env['sale.order'].create({'partner_id': cls.partner.id})
        cls.image = cls._create_attachment('photo.png', b'\x89PNG\r\n\x1a\n', 'image/png')
        cls.pdf = cls._create_attachment('quote.pdf', b'%PDF-1.4 test', 'application/pdf')

    @classmethod
    def _create_attachment(cls, name, content, mimetype):
        """Create an attachment with the given content."""
        return cls.env['ir.attachment'].create({
            'name': name,
            'datas': base64.b64encode(content).decode(),
            'mimetype': mimetype,
        })

    def test_field_definition(self):
        """The order has a many2many field to attachments."""
        field = self.env['sale.order']._fields['attachment_ids']
        self.assertEqual(field.type, 'many2many')
        self.assertEqual(field.comodel_name, 'ir.attachment')
        self.assertEqual(field.string, 'Attachments')

    def test_add_attachments(self):
        """Several attachments can be linked to an order."""
        self.order.attachment_ids = [(6, 0, (self.image | self.pdf).ids)]
        self.assertEqual(self.order.attachment_ids, self.image | self.pdf)
        self.assertEqual(
            sorted(self.order.attachment_ids.mapped('mimetype')),
            ['application/pdf', 'image/png'],
        )

    def test_remove_attachment(self):
        """Removing an attachment from the order keeps the file itself."""
        self.order.attachment_ids = [(6, 0, (self.image | self.pdf).ids)]
        self.order.attachment_ids = [(3, self.pdf.id)]
        self.assertEqual(self.order.attachment_ids, self.image)
        self.assertTrue(self.pdf.exists())

    def test_attachments_per_order(self):
        """Each order keeps its own attachments."""
        other_order = self.env['sale.order'].create({'partner_id': self.partner.id})
        self.order.attachment_ids = [(4, self.image.id)]
        other_order.attachment_ids = [(4, self.pdf.id)]
        self.assertEqual(self.order.attachment_ids, self.image)
        self.assertEqual(other_order.attachment_ids, self.pdf)

    def test_copy_order(self):
        """A duplicated order keeps the same attachments."""
        self.order.attachment_ids = [(6, 0, self.image.ids)]
        self.assertEqual(self.order.copy().attachment_ids, self.image)

    def test_form_view_widget(self):
        """The order form shows the field with the preview widget."""
        arch = self.env['sale.order'].get_view(view_type='form')['arch']
        fields = etree.fromstring(arch).xpath("//field[@name='attachment_ids']")
        self.assertEqual(len(fields), 1)
        self.assertEqual(fields[0].get('widget'), 'many2many_attachment_preview')

    def test_form_add_attachment(self):
        """Attachments can be added from the order form."""
        with Form(self.order) as order_form:
            order_form.attachment_ids.add(self.pdf)
        self.assertEqual(self.order.attachment_ids, self.pdf)

    def test_salesman_access(self):
        """A salesman can attach their own files to an order."""
        salesman = self.env['res.users'].create({
            'name': 'Salesman',
            'login': 'salesman_attachment',
            'group_ids': [(6, 0, self.env.ref('sales_team.group_sale_salesman_all_leads').ids)],
        })
        order = self.order.with_user(salesman)
        attachment = self.env['ir.attachment'].with_user(salesman).create({
            'name': 'note.txt',
            'datas': base64.b64encode(b'note').decode(),
        })
        order.attachment_ids = [(4, attachment.id)]
        self.assertEqual(order.attachment_ids.name, 'note.txt')

    def test_widget_assets(self):
        """The widget's files are loaded in the backend."""
        paths = [path for path, *_ in self.env['ir.asset']._get_asset_paths('web.assets_backend', {})]
        self.assertIn('/many2many_attachment_preview/static/src/js/attachment_preview.js', paths)
        self.assertIn('/many2many_attachment_preview/static/src/xml/attachment_preview.xml', paths)
