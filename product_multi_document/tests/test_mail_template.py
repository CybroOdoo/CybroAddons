# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE,ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
###############################################################################
import base64
from odoo.tests.common import TransactionCase

class TestMailTemplate(TransactionCase):
    """Test cases for mail.template attachment generation"""

    @classmethod
    def setUpClass(cls):

        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Vendor',
        })

        # Reuse an existing product to avoid publish_date NOT NULL issues
        cls.product = cls.env['product.product'].search([], limit=1)

        cls.document = cls.env['documents.document'].create({
            'name': 'Test Document',
            'datas': base64.b64encode(b'Test File Content'),
            'type': 'binary',
            'mimetype': 'text/plain',
        })

        cls.product.product_tmpl_id.write({
            'document_ids': [(4, cls.document.id)],
        })

        cls.purchase_order = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
        })


        cls.order_line = cls.env['purchase.order.line'].create({
            'order_id': cls.purchase_order.id,
            'product_id': cls.product.id,
            'name': cls.product.name,
            'product_qty': 1,
            'price_unit': 100,
            'date_planned': '2026-05-22',
        })

        cls.mail_template = cls.env['mail.template'].create({
            'name': 'PO Template',
            'model_id': cls.env.ref('purchase.model_purchase_order').id,
            'subject': 'Test Purchase Order',
            'body_html': '<p>Test</p>',
        })

    def test_generate_template_attachments(self):
        """Test product documents are added as attachments."""


        result = self.mail_template._generate_template_attachments(
            [self.purchase_order.id],
            ['subject'],
        )

        # The result must contain an entry for the purchase order
        self.assertIn(
            self.purchase_order.id,
            result,
            "Result must contain an entry for the purchase order",
        )

        order_result = result[self.purchase_order.id]

        self.assertIn(
            'attachments',
            order_result,
            "'attachments' key must be present after "
            "_generate_template_attachments",
        )

        attachments = order_result['attachments']


        self.assertTrue(attachments, "Attachments list must not be empty")

        attachment_names = [att[0] for att in attachments]


        self.assertIn(
            self.document.name,
            attachment_names,
            "Product document name must appear in the attachment list",
        )

        # Verify the attachment content is valid base64
        for name, data in attachments:
            if name == self.document.name:
                decoded = base64.b64decode(data)


                self.assertEqual(
                    decoded,
                    b'Test File Content',
                    "Attachment content must match "
                    "the original document bytes",
                )


    def test_generate_template_attachments_no_documents(self):
        """When order lines have no documents, method must not fail."""

        # Create a product with no documents
        product_no_doc = self.env['product.product'].search(
            [('product_tmpl_id.document_ids', '=', False)],
            limit=1
        )

        if not product_no_doc:
            self.skipTest("No product without documents available")


        order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })

        self.env['purchase.order.line'].create({
            'order_id': order.id,
            'product_id': product_no_doc.id,
            'name': product_no_doc.name,
            'product_qty': 1,
            'price_unit': 50,
            'date_planned': '2026-05-22',
        })

        # Must not raise KeyError or any other exception
        try:
            result = self.mail_template._generate_template_attachments(
                [order.id],
                ['subject'],
            )


        except KeyError as e:

            self.fail(
                f"_generate_template_attachments raised KeyError: {e}"
            )

        self.assertIn(order.id, result)


    def test_non_purchase_order_template_unaffected(self):
        """Templates other than purchase.order should remain unaffected."""


        sale_model = self.env['ir.model'].search(
            [('model', '=', 'sale.order')],
            limit=1
        )

        if not sale_model:
            self.skipTest("sale.order model not available")

        so_template = self.env['mail.template'].create({
            'name': 'SO Template',
            'model_id': sale_model.id,
            'subject': 'Test Sale Order',
            'body_html': '<p>SO Test</p>',
        })

        partner = self.env['res.partner'].create({
            'name': 'SO Customer'
        })

        sale_order = self.env['sale.order'].create({
            'partner_id': partner.id
        })

        result = so_template._generate_template_attachments(
            [sale_order.id],
            ['subject'],
        )

        self.assertIn(sale_order.id, result)

        attachments = result[sale_order.id].get('attachments', [])
        self.assertIsInstance(result, dict)


