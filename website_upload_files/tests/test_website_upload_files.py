import base64
import io
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from odoo.addons.website_sale.controllers import main
from odoo.addons.website_upload_files.controllers.website_upload_files import (
    WebsiteSaleFileUpload,
)


class FakeResponse:

    def __init__(self, order):
        self.qcontext = {'order': order}


class UploadedFile(io.BytesIO):

    def __init__(self, filename, content):
        super().__init__(content)
        self.filename = filename


class FakeRequest:

    def __init__(self, env):
        self.env = env


@tagged('post_install', '-at_install')
class TestWebsiteSaleFileUpload(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Website Upload Customer',
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
        })

    def _call_shop_payment(self, controller, **post):
        endpoint = getattr(controller.shop_payment, 'original_endpoint', None)
        if endpoint:
            return endpoint(controller, **post)
        return controller.shop_payment(**post)

    def _call_shop_attachments(self, controller, **post):
        endpoint = getattr(controller.shop_attachments, 'original_endpoint',
                           None)
        if endpoint:
            return endpoint(controller, **post)
        return controller.shop_attachments(**post)

    def test_shop_payment_creates_attachment_and_updates_qcontext(self):
        controller = WebsiteSaleFileUpload()
        upload = UploadedFile('proof.txt', b'proof content')

        def parent_shop_payment(_controller, **post):
            return FakeResponse(self.sale_order)

        with patch.object(main.WebsiteSale, 'shop_payment',
                          parent_shop_payment), patch(
                'odoo.addons.website_upload_files.controllers.'
                'website_upload_files.request',
                FakeRequest(self.env),
        ):
            response = self._call_shop_payment(
                controller,
                attachment=upload,
            )

        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', self.sale_order.id),
            ('name', '=', 'proof.txt'),
        ])
        self.assertEqual(len(attachment), 1)
        self.assertEqual(attachment.name, 'proof.txt')
        self.assertEqual(attachment.res_model, 'sale.order')
        self.assertEqual(attachment.res_id, self.sale_order.id)
        self.assertEqual(base64.b64decode(attachment.datas), b'proof content')
        self.assertIn(attachment.id, response.qcontext['attachment'].ids)

    def test_shop_payment_adds_existing_attachments_to_qcontext(self):
        controller = WebsiteSaleFileUpload()
        attachment = self.env['ir.attachment'].create({
            'name': 'existing.txt',
            'res_name': 'existing.txt',
            'type': 'binary',
            'res_model': 'sale.order',
            'res_id': self.sale_order.id,
            'datas': base64.b64encode(b'existing content'),
        })

        def parent_shop_payment(_controller, **post):
            return FakeResponse(self.sale_order)

        with patch.object(main.WebsiteSale, 'shop_payment',
                          parent_shop_payment), patch(
                'odoo.addons.website_upload_files.controllers.'
                'website_upload_files.request',
                FakeRequest(self.env),
        ):
            response = self._call_shop_payment(controller)

        self.assertIn(attachment.id, response.qcontext['attachment'].ids)

    def test_shop_attachments_deletes_attachment(self):
        controller = WebsiteSaleFileUpload()
        attachment = self.env['ir.attachment'].create({
            'name': 'delete-me.txt',
            'res_name': 'delete-me.txt',
            'type': 'binary',
            'res_model': 'sale.order',
            'res_id': self.sale_order.id,
            'datas': base64.b64encode(b'delete content'),
        })

        with patch(
                'odoo.addons.website_upload_files.controllers.'
                'website_upload_files.request',
                FakeRequest(self.env),
        ):
            result = self._call_shop_attachments(
                controller,
                attachment_id=attachment.id,
            )

        self.assertEqual(result, 1)
        self.assertFalse(attachment.exists())
