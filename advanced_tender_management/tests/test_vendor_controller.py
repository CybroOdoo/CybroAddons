# -*- coding: utf-8 -*-
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

from odoo.addons.advanced_tender_management.controllers.vendor import Vendor

from .common import TenderManagementTestCommon


class _LogoFile:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return self._payload


class TestVendorController(TenderManagementTestCommon):
    """Tests for vendor registration controller."""

    def _request(self):
        rendered = {}
        req = SimpleNamespace(
            env=self.env,
            user=self.env.user,
            render=lambda template, values=None: rendered.update({
                'template': template,
                'values': values or {},
            }) or rendered,
        )
        req.env.user = self.env.user
        req.rendered = rendered
        return req

    def test_render_vendor_template(self):
        controller = Vendor()
        req = self._request()

        with patch('odoo.addons.advanced_tender_management.controllers.vendor.request', req):
            result = controller.render_vendor_template()

        self.assertEqual(result['template'], 'advanced_tender_management.vendor_register_template')
        self.assertTrue(result['values']['tender_category'])
        self.assertTrue(result['values']['countries'])

    def test_register_vendor_with_auto_approval_creates_portal_user(self):
        self.env['ir.config_parameter'].sudo().set_param('advanced_tender_management.auto_approval', 'True')
        controller = Vendor()
        req = self._request()

        with patch('odoo.addons.mail.models.mail_template.MailTemplate.send_mail'), \
                patch('odoo.addons.advanced_tender_management.controllers.vendor.request', req):
            result = controller.register_vendor(
                company_logo=_LogoFile(b'logo'),
                name='New Vendor',
                street='Street',
                street2='Street 2',
                state=self.state.id,
                city='Kochi',
                country=self.country.id,
                zip='682001',
                vendor_type='company',
                phone='1234567890',
                email='newvendor@example.com',
                website='https://example.com',
                many2many_field=str([self.category.id]),
            )

        vendor = self.env['res.partner'].search([('email', '=', 'newvendor@example.com')], limit=1)
        user = self.env['res.users'].search([('partner_id', '=', vendor.id)], limit=1)
        self.assertEqual(result['template'], 'advanced_tender_management.register_thankyou_page')
        self.assertTrue(vendor.is_vendor)
        self.assertTrue(user)
        self.assertTrue(user.has_group('base.group_portal'))

    def test_register_vendor_with_manual_approval_sends_notification(self):
        self.env['ir.config_parameter'].sudo().set_param('advanced_tender_management.auto_approval', '')
        self.env['ir.config_parameter'].sudo().set_param(
            'advanced_tender_management.manual_approval_users_ids',
            str([self.env.user.id]),
        )
        controller = Vendor()
        req = self._request()

        with patch('odoo.addons.mail.models.mail_template.MailTemplate.send_mail') as send_mail, \
                patch('odoo.addons.advanced_tender_management.controllers.vendor.request', req):
            controller.register_vendor(
                company_logo=_LogoFile(b'logo'),
                name='Manual Vendor',
                street='Street',
                street2='Street 2',
                state=self.state.id,
                city='Kochi',
                country=self.country.id,
                zip='682001',
                vendor_type='individual',
                phone='1234567890',
                email='manualvendor@example.com',
                website='https://example.com',
                many2many_field=str([self.category.id]),
            )

        self.assertGreaterEqual(send_mail.call_count, 2)
