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
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestQuotationCustomerFollowup(TransactionCase):
    """Tests for quotation expiry and follow-up configuration."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Quotation Followup Customer',
            'email': 'customer@example.com',
        })

    def _create_order(self, **values):
        vals = {
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
        }
        vals.update(values)
        return self.env['sale.order'].create(vals)

    def test_partner_quotation_expiry_days(self):
        """The customer field stores the configured quotation expiry period."""
        self.partner.quotation_expiry_days = 14
        self.assertEqual(self.partner.quotation_expiry_days, 14)

    def test_settings_save_configuration_parameters(self):
        """Settings persist both email templates and their schedule values."""
        template = self.env['mail.template'].create({
            'name': 'Quotation Followup Test Template',
            'model_id': self.env.ref('sale.model_sale_order').id,
        })
        settings = self.env['res.config.settings'].create({
            'mail_template_id': template.id,
            'expiry_mail_id': template.id,
            'quotation_followup_mail': True,
            'quotation_expiry_mail': True,
            'days': 5,
            'expiry_days': 10,
        })
        settings.execute()
        params = self.env['ir.config_parameter'].sudo()

        self.assertEqual(params.get_str('quotation_customer_followup.mail_template'),
                         str(template.id))
        self.assertEqual(params.get_str('quotation_customer_followup.expiry_mail_template'),
                         str(template.id))
        self.assertEqual(params.get_int('quotation_customer_followup.days'), 5)
        self.assertEqual(params.get_int('quotation_customer_followup.expiry_days'), 10)
        self.assertTrue(params.get_bool('quotation_customer_followup.followup_enable'))
        self.assertTrue(params.get_bool('quotation_customer_followup.expiry_enable'))

    def test_partner_expiry_days_set_validity_date_onchange(self):
        """A customer's expiry period takes precedence when partner changes."""
        self.partner.quotation_expiry_days = 12
        order = self._create_order()
        order._compute_validity_date()

        self.assertEqual(
            order.validity_date,
            fields.Date.add(fields.Date.to_date(order.date_order), days=12),
        )

    def test_followup_scheduler_without_template_is_noop(self):
        """The scheduled follow-up exits safely when no template is configured."""
        self.env['ir.config_parameter'].sudo().set_str(
            'quotation_customer_followup.mail_template', False)
        self.env['sale.order'].followup_scheduler_queue()

    def test_expiry_scheduler_without_template_is_noop(self):
        """The scheduled expiry job exits safely when no template is configured."""
        self.env['ir.config_parameter'].sudo().set_str(
            'quotation_customer_followup.expiry_mail_template', False)
        self.env['sale.order'].process_scheduler_quotation()

    def test_expired_sent_quotation_uses_expiry_date_domain(self):
        """Only sent quotations with validity dates up to today are eligible."""
        order = self._create_order(
            state='sent',
            validity_date=fields.Date.today() - timedelta(days=1),
        )
        eligible = self.env['sale.order'].search([
            ('state', '=', 'sent'),
            ('validity_date', '<=', fields.Date.today()),
        ])
        self.assertIn(order, eligible)

    def test_schedulers_disabled_toggles_are_noop(self):
        """Schedulers exit early when feature toggles are disabled."""
        template = self.env['mail.template'].create({
            'name': 'Test Template Disabled Toggles',
            'model_id': self.env.ref('sale.model_sale_order').id,
        })
        params = self.env['ir.config_parameter'].sudo()
        params.set_bool('quotation_customer_followup.expiry_enable', False)
        params.set_bool('quotation_customer_followup.followup_enable', False)
        params.set_str('quotation_customer_followup.expiry_mail_template', str(template.id))
        params.set_str('quotation_customer_followup.mail_template', str(template.id))
        params.set_int('quotation_customer_followup.days', 1)

        self._create_order(
            state='sent',
            validity_date=fields.Date.today() - timedelta(days=2),
            user_id=False,
        )

        with patch.object(type(template), 'send_mail') as mock_send_mail:
            self.env['sale.order'].process_scheduler_quotation()
            self.env['sale.order'].followup_scheduler_queue()
            mock_send_mail.assert_not_called()

    def test_schedulers_handle_empty_salesperson(self):
        """Schedulers do not crash and handle email_from safely when user_id is empty."""
        template = self.env['mail.template'].create({
            'name': 'Test Template Empty Salesperson',
            'model_id': self.env.ref('sale.model_sale_order').id,
        })
        params = self.env['ir.config_parameter'].sudo()
        params.set_bool('quotation_customer_followup.expiry_enable', True)
        params.set_str('quotation_customer_followup.expiry_mail_template', str(template.id))

        order = self._create_order(
            state='sent',
            validity_date=fields.Date.today() - timedelta(days=1),
            user_id=False,
        )

        with patch.object(type(template), 'send_mail') as mock_send_mail:
            self.env['sale.order'].process_scheduler_quotation()
            self.assertTrue(mock_send_mail.called)
            order_calls = [
                call for call in mock_send_mail.call_args_list
                if call[0][0] == order.id
            ]
            self.assertTrue(order_calls, "Expected send_mail to be called for the created order")
            kwargs = order_calls[0].kwargs or order_calls[0][1]
            email_values = kwargs.get('email_values', {})
            self.assertEqual(email_values.get('email_to'), self.partner.email)
            if 'email_from' in email_values:
                self.assertTrue(bool(email_values['email_from']))

    def test_settings_expiry_days_set_validity_date_fallback(self):
        """When partner has no expiry period, the settings expiry_days value is used."""
        self.partner.quotation_expiry_days = False
        self.env['ir.config_parameter'].sudo().set_int(
            'quotation_customer_followup.expiry_days', 15)
        order = self._create_order()
        order._compute_validity_date()

        self.assertEqual(
            order.validity_date,
            fields.Date.add(fields.Date.to_date(order.date_order), days=15),
        )

    def test_zero_expiry_days_preserves_core_validity_date(self):
        """When expiry days are 0, validity_date is not overridden with date_order."""
        self.partner.quotation_expiry_days = 0
        self.env['ir.config_parameter'].sudo().set_int(
            'quotation_customer_followup.expiry_days', 0)
        order = self._create_order()
        order._compute_validity_date()

        # If company quotation validity is 0, validity_date remains False, NOT forced to date_order
        if order.company_id.quotation_validity_days == 0:
            self.assertFalse(order.validity_date)
        else:
            self.assertNotEqual(order.validity_date, fields.Date.to_date(order.date_order))

    def test_process_scheduler_quotation_sends_mail(self):
        """Expired sent quotation triggers mail sending using the configured expiry template."""
        template = self.env['mail.template'].create({
            'name': 'Quotation Expiry Email Template',
            'model_id': self.env.ref('sale.model_sale_order').id,
        })
        params = self.env['ir.config_parameter'].sudo()
        params.set_bool('quotation_customer_followup.expiry_enable', True)
        params.set_str('quotation_customer_followup.expiry_mail_template', str(template.id))

        order = self._create_order(
            state='sent',
            validity_date=fields.Date.today() - timedelta(days=1),
        )

        with patch.object(type(template), 'send_mail') as mock_send_mail:
            self.env['sale.order'].process_scheduler_quotation()
            self.assertTrue(mock_send_mail.called)
            called_order_ids = [call[0][0] for call in mock_send_mail.call_args_list]
            self.assertIn(order.id, called_order_ids)

    def test_followup_scheduler_queue_sends_mail(self):
        """Sent quotation past the follow-up days threshold triggers follow-up email."""
        template = self.env['mail.template'].create({
            'name': 'Quotation Followup Email Template',
            'model_id': self.env.ref('sale.model_sale_order').id,
        })
        params = self.env['ir.config_parameter'].sudo()
        params.set_bool('quotation_customer_followup.followup_enable', True)
        params.set_str('quotation_customer_followup.mail_template', str(template.id))
        params.set_int('quotation_customer_followup.days', 3)

        order = self._create_order(
            state='sent',
            date_order=fields.Datetime.now() - timedelta(days=5),
        )

        with patch.object(type(template), 'send_mail') as mock_send_mail:
            self.env['sale.order'].followup_scheduler_queue()
            self.assertTrue(mock_send_mail.called)
            called_order_ids = [call[0][0] for call in mock_send_mail.call_args_list]
            self.assertIn(order.id, called_order_ids)



