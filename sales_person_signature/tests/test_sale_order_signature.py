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

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSaleOrderSignature(TransactionCase):
    """Test suite for salesperson signature feature and configuration."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config_param = cls.env['ir.config_parameter'].sudo()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
        })
        cls.salesperson = cls.env['res.users'].create({
            'name': 'Test Salesperson',
            'login': 'test_salesperson_user',
            'email': 'salesperson@test.example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id,
                                  cls.env.ref('sales_team.group_sale_salesman').id])],
        })
        cls.other_user = cls.env['res.users'].create({
            'name': 'Test Other User',
            'login': 'test_other_user',
            'email': 'other@test.example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id,
                                  cls.env.ref('sales_team.group_sale_salesman_all_leads').id])],
        })
        cls.sample_signature = base64.b64encode(b'sample signature content').decode('utf-8')

    def test_01_res_config_settings(self):
        """Test enabling and disabling the sale document approval config parameter."""
        settings = self.env['res.config.settings'].create({
            'is_sale_document_approve': True,
        })
        settings.execute()
        self.assertTrue(
            self.config_param.get_bool('sales_person_signature.sale_document_approve'),
            "Config parameter should be True after enabling in settings.",
        )

        settings = self.env['res.config.settings'].create({
            'is_sale_document_approve': False,
        })
        settings.execute()
        self.assertFalse(
            self.config_param.get_bool('sales_person_signature.sale_document_approve'),
            "Config parameter should be False after disabling in settings.",
        )

    def test_02_signature_flags_computation(self):
        """Test computation of helper boolean flags on sale orders."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'user_id': self.salesperson.id,
        })

        # 1. Approval disabled
        self.config_param.set_bool('sales_person_signature.sale_document_approve', False)
        order.invalidate_recordset()
        self.assertFalse(order.is_settings_approval)
        self.assertFalse(order.is_user_salesperson)
        self.assertFalse(order.is_check_signature)

        # 2. Approval enabled, accessed by salesperson without signature
        self.config_param.set_bool('sales_person_signature.sale_document_approve', True)
        order_salesperson = order.with_user(self.salesperson)
        order_salesperson.invalidate_recordset()
        self.assertTrue(order_salesperson.is_settings_approval)
        self.assertTrue(order_salesperson.is_user_salesperson)
        self.assertFalse(order_salesperson.is_check_signature)

        # 3. Approval enabled, accessed by another user
        order_other = order.with_user(self.other_user)
        order_other.invalidate_recordset()
        self.assertTrue(order_other.is_settings_approval)
        self.assertFalse(order_other.is_user_salesperson)
        self.assertFalse(order_other.is_check_signature)

        # 4. Signature added
        order.sale_person_signature = self.sample_signature
        order.invalidate_recordset()
        self.assertTrue(order.is_check_signature)

    def test_03_action_confirm_enforcement(self):
        """Test backend enforcement in action_confirm."""
        self.config_param.set_bool('sales_person_signature.sale_document_approve', True)

        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'user_id': self.salesperson.id,
        })

        # Confirming without signature when approval is enabled must raise ValidationError
        with self.assertRaises(ValidationError):
            order.action_confirm()

        # Adding signature allows confirmation
        order.sale_person_signature = self.sample_signature
        order.action_confirm()
        self.assertEqual(order.state, 'sale')

    def test_04_action_confirm_without_approval(self):
        """Test that orders can be confirmed without signature when approval is disabled."""
        self.config_param.set_bool('sales_person_signature.sale_document_approve', False)

        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'user_id': self.salesperson.id,
        })

        # Confirming without signature should succeed
        order.action_confirm()
        self.assertEqual(order.state, 'sale')

    def test_05_quotation_template_integration(self):
        """Test integration with sale_management quotation templates."""
        template = self.env['sale.order.template'].create({
            'name': 'Standard Quotation Template',
        })
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'user_id': self.salesperson.id,
            'sale_order_template_id': template.id,
        })
        self.config_param.set_bool('sales_person_signature.sale_document_approve', True)
        order_salesperson = order.with_user(self.salesperson)
        order_salesperson.invalidate_recordset()
        self.assertTrue(order_salesperson.is_settings_approval)
        self.assertTrue(order_salesperson.is_user_salesperson)
        self.assertEqual(order.sale_order_template_id, template)
