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
import io
import json
from types import SimpleNamespace
from unittest.mock import patch

from werkzeug.datastructures import MultiDict

from odoo.tests import tagged

from odoo.addons.advanced_tender_management.controllers.vendor import Vendor

from .common import TenderManagementTestCommon


# 1x1 transparent PNG
PNG_PIXEL = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==')


class _LogoFile(io.BytesIO):
    pass


@tagged('post_install', '-at_install')
class TestVendorController(TenderManagementTestCommon):
    """Tests for vendor registration controller."""

    def _request(self, categories=()):
        return SimpleNamespace(
            env=self.env,
            httprequest=SimpleNamespace(form=MultiDict(
                [('category', str(cat_id)) for cat_id in categories])),
            render=lambda template, values=None: {'template': template, 'values': values or {}},
        )

    def _register(self, req, email, **extra):
        values = {
            'company_logo': _LogoFile(PNG_PIXEL),
            'name': 'New Vendor',
            'street': 'Street',
            'street2': 'Street 2',
            'state': str(self.state.id),
            'city': 'Kochi',
            'country': str(self.country.id),
            'zip': '682001',
            'phone': '1234567890',
            'email': email,
            'website': 'https://example.com',
        }
        values.update(extra)
        return self.call_route(Vendor().register_vendor, **values)

    def test_render_vendor_template(self):
        with patch('odoo.addons.advanced_tender_management.controllers.vendor.request',
                   self._request()):
            result = self.call_route(Vendor().render_vendor_template)

        self.assertEqual(result['template'], 'advanced_tender_management.vendor_register_template')
        self.assertTrue(result['values']['tender_category'])
        self.assertTrue(result['values']['countries'])

    def test_register_vendor_with_auto_approval_creates_portal_user(self):
        self.env['ir.config_parameter'].sudo().set_bool(
            'advanced_tender_management.auto_approval', True)
        other_category = self.env['tender.category'].create({'name': 'Medical'})
        req = self._request(categories=[self.category.id, other_category.id])

        with patch('odoo.addons.mail.models.mail_template.MailTemplate.send_mail'), \
                patch('odoo.addons.mail.models.mail_template.MailTemplate.send_mail_batch',
                      autospec=True) as send_mail_batch, \
                patch('odoo.addons.advanced_tender_management.controllers.vendor.request', req):
            result = self._register(req, 'newvendor@example.com')

        vendor = self.env['res.partner'].search([('email', '=', 'newvendor@example.com')], limit=1)
        user = self.env['res.users'].search([('partner_id', '=', vendor.id)], limit=1)
        self.assertEqual(result['template'], 'advanced_tender_management.register_thankyou_page')
        self.assertTrue(vendor.is_vendor)
        self.assertEqual(vendor.state_id, self.state)
        self.assertEqual(vendor.tender_category_ids, self.category | other_category)
        self.assertTrue(user.has_group('base.group_portal'))
        self.assertTrue(vendor.image_1920)
        # The vendor is invited to set a password, so the account is usable
        self.assertEqual(vendor.sudo().signup_type, 'signup')
        invitation = self.env.ref('auth_signup.portal_set_password_email')
        self.assertIn((invitation, user.ids),
                      [(call.args[0], call.args[1]) for call in send_mail_batch.call_args_list])

    def test_register_vendor_with_manual_approval_sends_notification(self):
        params = self.env['ir.config_parameter'].sudo()
        params.set_bool('advanced_tender_management.auto_approval', False)
        params.set_str('advanced_tender_management.manual_approval_users_ids',
                       json.dumps([self.env.user.id]))
        req = self._request(categories=[self.category.id])

        with patch('odoo.addons.mail.models.mail_template.MailTemplate.send_mail') as send_mail, \
                patch('odoo.addons.advanced_tender_management.controllers.vendor.request', req):
            self._register(req, 'manualvendor@example.com', state='',
                           company_logo=_LogoFile(b'not an image'))

        vendor = self.env['res.partner'].search([('email', '=', 'manualvendor@example.com')])
        self.assertFalse(vendor.state_id)
        self.assertFalse(vendor.image_1920)
        self.assertFalse(self.env['res.users'].search([('partner_id', '=', vendor.id)]))
        self.assertEqual(send_mail.call_count, 2)
