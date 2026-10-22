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
import io
from unittest.mock import patch

from PIL import Image

from werkzeug.wrappers import Response

from odoo.tests import HttpCase, TransactionCase, tagged

from odoo.addons.website_sale.controllers import main
from odoo.addons.website_sale.tests.common import MockRequest
from odoo.addons.website_upload_files.controllers.website_upload_files import (
    WebsiteSaleFileUpload,
)

CONTROLLER = 'odoo.addons.website_upload_files.controllers.website_upload_files'


class FakePage:
    """Payment page returned by the parent controller"""

    def __init__(self):
        self.qcontext = {}


class UploadedFile(io.BytesIO):
    """File posted from the payment page form"""

    def __init__(self, filename, content):
        super().__init__(content)
        self.filename = filename


class UploadCommon:
    """Orders and helpers shared by the controller tests"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = (cls.env.company.website_id
                       or cls.env['website'].search([], limit=1))
        cls.partner = cls.env['res.partner'].create({'name': 'Customer'})
        cls.order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'website_id': cls.website.id,
        })
        cls.other_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'website_id': cls.website.id,
        })
        cls.salesman = cls.env['res.users'].create({
            'name': 'Salesman',
            'login': 'upload_salesman',
            'group_ids': [(6, 0, cls.env.ref(
                'sales_team.group_sale_salesman_all_leads').ids)],
        })

    def _attach(self, order, name, env=None):
        """Create an attachment on the order"""
        return (env or self.env)['ir.attachment'].create({
            'name': name,
            'type': 'binary',
            'res_model': 'sale.order',
            'res_id': order.id,
            'raw': b'content',
        })


@tagged('post_install', '-at_install')
class TestWebsiteSaleFileUpload(UploadCommon, TransactionCase):
    """Tests for the payment page upload and delete routes"""

    def _shop_payment(self, parent_response, **post):
        """Call the payment page with the parent controller mocked"""
        controller = WebsiteSaleFileUpload()
        with patch.object(main.WebsiteSale, 'shop_payment',
                          lambda _self, **kw: parent_response), \
                MockRequest(self.env, website=self.website,
                            sale_order_id=self.order.id):
            return controller.shop_payment.original_endpoint(controller, **post)

    def _shop_attachments(self, attachment_id, order=None):
        """Call the delete route for the current cart"""
        controller = WebsiteSaleFileUpload()
        with MockRequest(self.env, website=self.website,
                         sale_order_id=(order or self.order).id):
            return controller.shop_attachments.original_endpoint(
                controller, attachment_id=attachment_id)

    def _order_files(self, order=None):
        return self.env['ir.attachment'].search([
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', (order or self.order).id),
        ])

    def test_upload_file(self):
        """An uploaded file is attached to the cart and listed."""
        page = self._shop_payment(
            FakePage(), attachment=UploadedFile('proof.txt', b'proof content'))
        attachment = self._order_files()
        self.assertEqual(attachment.name, 'proof.txt')
        self.assertEqual(bytes(attachment.raw), b'proof content')
        self.assertEqual(attachment.mimetype, 'text/plain')
        self.assertEqual(page.qcontext['attachment'], attachment)
        self.assertFalse(page.qcontext['attachment_error'])

    def test_upload_image(self):
        """Images are accepted."""
        image = io.BytesIO()
        Image.new('RGB', (2, 2), 'red').save(image, 'PNG')
        self._shop_payment(FakePage(), attachment=UploadedFile(
            'photo.png', image.getvalue()))
        self.assertEqual(self._order_files().mimetype, 'image/png')

    def test_upload_too_large(self):
        """Files over the size limit are refused."""
        with patch(f'{CONTROLLER}.MAX_FILE_SIZE', 5):
            page = self._shop_payment(
                FakePage(), attachment=UploadedFile('big.txt', b'too large'))
        self.assertFalse(self._order_files())
        self.assertIn('10 MB', page.qcontext['attachment_error'])

    def test_upload_wrong_type(self):
        """Files of other types are refused."""
        page = self._shop_payment(FakePage(), attachment=UploadedFile(
            'tool.exe', b'MZ\x90\x00\x03\x00\x00\x00\x04\x00'))
        self.assertFalse(self._order_files())
        self.assertIn('not allowed', page.qcontext['attachment_error'])

    def test_upload_empty_file(self):
        """Empty files are refused."""
        page = self._shop_payment(
            FakePage(), attachment=UploadedFile('empty.txt', b''))
        self.assertFalse(self._order_files())
        self.assertTrue(page.qcontext['attachment_error'])

    def test_parent_redirect(self):
        """A redirect from the checkout is returned as it is."""
        redirect = Response(status=303, headers={'Location': '/shop/cart'})
        response = self._shop_payment(
            redirect, attachment=UploadedFile('proof.txt', b'proof content'))
        self.assertIs(response, redirect)
        self.assertFalse(self._order_files())

    def test_list_only_own_files(self):
        """Files added by the sales team are not listed to the customer."""
        staff_file = self._attach(self.order, 'quotation.pdf',
                                  self.env(user=self.salesman))
        own_file = self._attach(self.order, 'mine.txt')
        page = self._shop_payment(FakePage())
        self.assertEqual(page.qcontext['attachment'], own_file)
        self.assertNotIn(staff_file, page.qcontext['attachment'])

    def test_delete_own_file(self):
        """Customers can delete a file they uploaded on their cart."""
        attachment = self._attach(self.order, 'mine.txt')
        self.assertEqual(self._shop_attachments(attachment.id), 1)
        self.assertFalse(attachment.exists())

    def test_delete_other_order_file(self):
        """Files of another order cannot be deleted."""
        attachment = self._attach(self.other_order, 'other.txt')
        self.assertEqual(self._shop_attachments(attachment.id), 0)
        self.assertTrue(attachment.exists())

    def test_delete_staff_file(self):
        """Files added by the sales team cannot be deleted by the customer."""
        attachment = self._attach(self.order, 'quotation.pdf',
                                  self.env(user=self.salesman))
        self.assertEqual(self._shop_attachments(attachment.id), 0)
        self.assertTrue(attachment.exists())

    def test_delete_invalid_id(self):
        """Invalid ids are ignored."""
        self.assertEqual(self._shop_attachments('abc'), 0)
        self.assertEqual(self._shop_attachments(None), 0)


@tagged('post_install', '-at_install')
class TestWebsiteUploadHttp(UploadCommon, HttpCase):
    """Real HTTP requests to the payment page and the delete route"""

    def _visitor_file(self, order, name):
        """Attachment uploaded by the public visitor"""
        return self._attach(order, name,
                            self.env(user=self.website.user_id, su=True))

    def test_payment_page_empty_cart(self):
        """The payment page with an empty cart redirects instead of failing."""
        response = self.url_open('/shop/payment', allow_redirects=False)
        self.assertIn(response.status_code, (302, 303))

    def test_delete_route(self):
        """The delete route only removes the visitor's own cart files."""
        own_file = self._visitor_file(self.order, 'mine.txt')
        other_file = self._visitor_file(self.other_order, 'other.txt')
        self.authenticate(None, None,
                          session_extra={'sale_order_id': self.order.id})
        result = self.make_jsonrpc_request(
            '/shop/attachments', {'attachment_id': other_file.id})
        self.assertEqual(result, 0)
        self.assertTrue(other_file.exists())
        result = self.make_jsonrpc_request(
            '/shop/attachments', {'attachment_id': own_file.id})
        self.assertEqual(result, 1)
        self.assertFalse(own_file.exists())

    def test_delete_route_without_cart(self):
        """Visitors without a cart cannot delete anything."""
        attachment = self._visitor_file(self.order, 'mine.txt')
        self.authenticate(None, None)
        result = self.make_jsonrpc_request(
            '/shop/attachments', {'attachment_id': attachment.id})
        self.assertEqual(result, 0)
        self.assertTrue(attachment.exists())
