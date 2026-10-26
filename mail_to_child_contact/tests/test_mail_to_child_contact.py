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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMailToChildContact(TransactionCase):
    """Test case for recipient expansion with child contacts."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_partner = cls.env['res.partner'].create({
            'name': 'Parent Company Partner',
            'is_company': True,
            'email': 'parent_company@test.com',
        })
        cls.child_1 = cls.env['res.partner'].create({
            'name': 'Child Contact 1',
            'parent_id': cls.company_partner.id,
            'email': 'child1@test.com',
        })
        cls.child_2 = cls.env['res.partner'].create({
            'name': 'Child Contact 2',
            'parent_id': cls.company_partner.id,
            'email': 'child2@test.com',
        })
        cls.child_no_mail = cls.env['res.partner'].create({
            'name': 'Child Contact No Email',
            'parent_id': cls.company_partner.id,
            'email': False,
        })

        cls.sale_template = cls.env.ref('sale.email_template_edi_sale', raise_if_not_found=False)
        if not cls.sale_template:
            cls.sale_template = cls.env['mail.template'].create({
                'name': 'Test Sale Template',
                'model_id': cls.env['ir.model']._get_id('sale.order'),
                'use_default_to': True,
            })

        cls.invoice_template = cls.env.ref('account.email_template_edi_invoice', raise_if_not_found=False)
        if not cls.invoice_template:
            cls.invoice_template = cls.env['mail.template'].create({
                'name': 'Test Invoice Template',
                'model_id': cls.env['ir.model']._get_id('account.move'),
                'use_default_to': True,
            })

    def test_sale_order_template_recipients_parent(self):
        """When sending a sale order with parent partner, all child contacts are added."""
        order = self.env['sale.order'].create({
            'partner_id': self.company_partner.id,
        })
        render_results = self.sale_template._generate_template_recipients(
            [order.id], ['partner_to', 'email_to']
        )
        recipient_partner_ids = render_results[order.id].get('partner_ids', [])
        self.assertIn(self.company_partner.id, recipient_partner_ids)
        self.assertIn(self.child_1.id, recipient_partner_ids)
        self.assertIn(self.child_2.id, recipient_partner_ids)

    def test_sale_order_template_recipients_child(self):
        """When sending a sale order with a child partner, siblings and parent are added."""
        order = self.env['sale.order'].create({
            'partner_id': self.child_1.id,
        })
        render_results = self.sale_template._generate_template_recipients(
            [order.id], ['partner_to', 'email_to']
        )
        recipient_partner_ids = render_results[order.id].get('partner_ids', [])
        self.assertIn(self.child_1.id, recipient_partner_ids)
        self.assertIn(self.child_2.id, recipient_partner_ids)
        self.assertIn(self.company_partner.id, recipient_partner_ids)

    def test_other_model_template_not_expanded(self):
        """Templates for other models (e.g. res.partner) should not expand recipients."""
        partner_template = self.env['mail.template'].create({
            'name': 'Test Other Template',
            'model_id': self.env['ir.model']._get_id('res.partner'),
            'use_default_to': True,
        })
        render_results = partner_template._generate_template_recipients(
            [self.company_partner.id], ['partner_to', 'email_to']
        )
        recipient_partner_ids = render_results[self.company_partner.id].get('partner_ids', [])
        self.assertIn(self.company_partner.id, recipient_partner_ids)
        self.assertNotIn(self.child_1.id, recipient_partner_ids)
        self.assertNotIn(self.child_2.id, recipient_partner_ids)

    def test_account_move_send_recipients_parent(self):
        """When getting recipients for account.move.send with parent, all child contacts are added."""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.company_partner.id,
        })
        partners = self.env['account.move.send']._get_default_mail_partner_ids(
            invoice, self.invoice_template, 'en_US'
        )
        self.assertIn(self.company_partner, partners)
        self.assertIn(self.child_1, partners)
        self.assertIn(self.child_2, partners)
        self.assertNotIn(self.child_no_mail, partners)

    def test_account_move_send_recipients_child(self):
        """When getting recipients for account.move.send with child, siblings and parent are added."""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.child_1.id,
        })
        partners = self.env['account.move.send']._get_default_mail_partner_ids(
            invoice, self.invoice_template, 'en_US'
        )
        self.assertIn(self.company_partner, partners)
        self.assertIn(self.child_1, partners)
        self.assertIn(self.child_2, partners)
