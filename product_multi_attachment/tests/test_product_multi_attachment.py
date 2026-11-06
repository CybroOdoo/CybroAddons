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
from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestProductMultiAttachment(TransactionCase):
    """Test product multi attachment features across products, sales,
    purchases, and email templates."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner Multi Attach',
            'email': 'partner@test.com',
        })

        # Attachments
        cls.attach_tmpl = cls.env['ir.attachment'].create({
            'name': 'Manual_Template.pdf',
            'type': 'binary',
            'raw': b'Template attachment content',
            'mimetype': 'application/pdf',
        })
        cls.attach_variant = cls.env['ir.attachment'].create({
            'name': 'Spec_Variant.pdf',
            'type': 'binary',
            'raw': b'Variant attachment content',
            'mimetype': 'application/pdf',
        })
        cls.attach_extra = cls.env['ir.attachment'].create({
            'name': 'Extra_Doc.txt',
            'type': 'binary',
            'raw': b'Extra line document',
            'mimetype': 'text/plain',
        })

        # Product with template attachments
        cls.product_tmpl = cls.env['product.template'].create({
            'name': 'Test Product Template with Attachments',
            'attachment_ids': [fields.Command.link(cls.attach_tmpl.id)],
        })
        cls.product_with_tmpl_attach = cls.product_tmpl.product_variant_id

        # Product with variant attachments
        cls.product_variant_only = cls.env['product.product'].create({
            'name': 'Test Product Variant with Attachments',
            'attachment_ids': [fields.Command.link(cls.attach_variant.id)],
        })

        # Product with no attachments
        cls.product_plain = cls.env['product.product'].create({
            'name': 'Plain Product No Attachments',
        })

    def test_01_product_attachments_setup(self):
        """Verify attachment setup on template and product variant."""
        self.assertIn(self.attach_tmpl, self.product_tmpl.attachment_ids)
        self.assertIn(
            self.attach_tmpl, self.product_with_tmpl_attach.product_tmpl_id.attachment_ids,
        )
        self.assertIn(
            self.attach_variant, self.product_variant_only.attachment_ids,
        )
        self.assertFalse(self.product_plain.attachment_ids)

    def test_02_sale_order_line_attachments(self):
        """Test attachment synchronization on sale order lines."""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                fields.Command.create({
                    'product_id': self.product_variant_only.id,
                    'product_uom_qty': 1,
                    'price_unit': 100.0,
                }),
                fields.Command.create({
                    'product_id': self.product_with_tmpl_attach.id,
                    'product_uom_qty': 2,
                    'price_unit': 50.0,
                }),
                fields.Command.create({
                    'product_id': self.product_plain.id,
                    'product_uom_qty': 1,
                    'price_unit': 10.0,
                }),
            ],
        })

        line_variant = sale_order.order_line[0]
        line_tmpl = sale_order.order_line[1]
        line_plain = sale_order.order_line[2]

        self.assertIn(self.attach_variant, line_variant.attachment_ids)
        self.assertIn(self.attach_tmpl, line_tmpl.attachment_ids)
        self.assertFalse(line_plain.attachment_ids)

        # Test manual addition of an extra attachment on the order line
        line_plain.attachment_ids = [fields.Command.link(self.attach_extra.id)]
        self.assertIn(self.attach_extra, line_plain.attachment_ids)

    def test_03_purchase_order_line_attachments(self):
        """Test attachment synchronization on purchase order lines."""
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                fields.Command.create({
                    'product_id': self.product_variant_only.id,
                    'product_qty': 1,
                    'price_unit': 80.0,
                }),
                fields.Command.create({
                    'product_id': self.product_with_tmpl_attach.id,
                    'product_qty': 3,
                    'price_unit': 40.0,
                }),
                fields.Command.create({
                    'product_id': self.product_plain.id,
                    'product_qty': 1,
                    'price_unit': 5.0,
                }),
            ],
        })

        line_variant = purchase_order.order_line[0]
        line_tmpl = purchase_order.order_line[1]
        line_plain = purchase_order.order_line[2]

        self.assertIn(self.attach_variant, line_variant.attachment_ids)
        self.assertIn(self.attach_tmpl, line_tmpl.attachment_ids)
        self.assertFalse(line_plain.attachment_ids)

        # Test manual addition of an extra attachment on the order line
        line_plain.attachment_ids = [fields.Command.link(self.attach_extra.id)]
        self.assertIn(self.attach_extra, line_plain.attachment_ids)

    def test_04_mail_template_generate_attachments_sale(self):
        """Test mail template generates product attachments for sale order."""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                fields.Command.create({
                    'product_id': self.product_variant_only.id,
                    'product_uom_qty': 1,
                    'price_unit': 100.0,
                }),
            ],
        })

        template = self.env['mail.template'].create({
            'name': 'Test Sale Order Template',
            'model_id': self.env['ir.model']._get_id('sale.order'),
            'subject': 'Quotation {{ object.name }}',
            'body_html': '<p>Here is your quotation</p>',
        })

        rendered = template._generate_template_attachments(
            [sale_order.id], ['attachment_ids'],
        )
        self.assertIn(sale_order.id, rendered)
        attached_ids = rendered[sale_order.id].get('attachment_ids', [])
        self.assertIn(self.attach_variant.id, attached_ids)

    def test_05_mail_template_generate_attachments_purchase(self):
        """Test mail template generates product attachments for purchase order."""
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                fields.Command.create({
                    'product_id': self.product_with_tmpl_attach.id,
                    'product_qty': 1,
                    'price_unit': 50.0,
                }),
            ],
        })

        template = self.env['mail.template'].create({
            'name': 'Test Purchase Order Template',
            'model_id': self.env['ir.model']._get_id('purchase.order'),
            'subject': 'RFQ {{ object.name }}',
            'body_html': '<p>Here is your RFQ</p>',
        })

        rendered = template._generate_template_attachments(
            [purchase_order.id], ['attachment_ids'],
        )
        self.assertIn(purchase_order.id, rendered)
        attached_ids = rendered[purchase_order.id].get('attachment_ids', [])
        self.assertIn(self.attach_tmpl.id, attached_ids)
