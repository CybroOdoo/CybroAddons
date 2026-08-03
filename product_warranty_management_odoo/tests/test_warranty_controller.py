from odoo.fields import Command
from odoo.tests import HttpCase, tagged
from odoo.tests.common import JsonRpcException


@tagged('post_install', '-at_install')
class TestWarrantyClaimController(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({'name': 'Warranty Public Customer'})
        cls.warranty_product = cls.env['product.product'].create({
            'name': 'Controller Warranty Product',
            'type': 'consu',
            'is_warranty_available': True,
            'warranty_duration': 24,
            'taxes_id': [Command.clear()],
        })
        cls.non_warranty_product = cls.env['product.product'].create({
            'name': 'Controller Non Warranty Product',
            'type': 'consu',
            'is_warranty_available': False,
            'taxes_id': [Command.clear()],
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.customer.id,
            'is_warranty_check': True,
            'order_line': [
                Command.create({
                    'product_id': cls.warranty_product.id,
                    'product_uom_qty': 1.0,
                }),
                Command.create({
                    'product_id': cls.non_warranty_product.id,
                    'product_uom_qty': 1.0,
                }),
            ],
        })

    def test_warranty_page_and_submit_page_render(self):
        warranty_response = self.url_open('/warranty')
        thanks_response = self.url_open('/warranty/claim/submit')

        self.assertIn('Warranty Claim Request', warranty_response.text)
        self.assertIn(self.customer.name, warranty_response.text)
        self.assertIn('Success!!!!', thanks_response.text)

    def test_get_sale_order_data(self):
        result = self.make_jsonrpc_request('/partner/sale_order', {
            'partner_id': self.customer.id,
        })
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], self.sale_order.id)
        self.assertEqual(result[0]['name'], self.sale_order.name)

    def test_get_sale_order_line_data(self):
        result = self.make_jsonrpc_request('/partner/sale_order_line', {
            'order_id': self.sale_order.id,
        })
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        product_ids = [line['product_id'][0] for line in result]
        self.assertIn(self.warranty_product.id, product_ids)
        self.assertIn(self.non_warranty_product.id, product_ids)

    def test_warranty_claim_count(self):
        self.env['warranty.claim'].create({
            'customer_id': self.customer.id,
            'sale_order_id': self.sale_order.id,
            'product_id': self.warranty_product.id,
        })

        result = self.make_jsonrpc_request('/partner/warranty_claim_count', {
            'sale_order_id': self.sale_order.id,
        })
        self.assertEqual(result, 1)

    def test_read_sale_order_returns_only_warranty_checked_orders(self):
        result = self.make_jsonrpc_request('/read/sale_order', {
            'order_id': self.sale_order.id,
        })
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], self.sale_order.id)
        self.assertTrue(result[0]['is_warranty_check'])

        non_warranty_sale_order = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'is_warranty_check': False,
        })
        non_warranty_result = self.make_jsonrpc_request('/read/sale_order', {
            'order_id': non_warranty_sale_order.id,
        })
        self.assertEqual(non_warranty_result, [])

    def test_check_selected_product_returns_only_warranty_products(self):
        warranty_result = self.make_jsonrpc_request('/check/selected_product', {
            'product_id': self.warranty_product.id,
        })
        non_warranty_result = self.make_jsonrpc_request('/check/selected_product', {
            'product_id': self.non_warranty_product.id,
        })

        self.assertIsInstance(warranty_result, list)
        if warranty_result:
            self.assertEqual(warranty_result[0]['id'], self.warranty_product.id)
            self.assertTrue(warranty_result[0]['is_warranty_available'])
        self.assertEqual(non_warranty_result, [])

    def test_create_warranty_claim(self):
        result = self.make_jsonrpc_request('/create_warranty_claim', {
            'sale_order_id': self.sale_order.id,
            'customer_id': self.customer.id,
            'product_id': self.warranty_product.id,
        })
        self.assertIsNone(result)

        claim = self.env['warranty.claim'].search([
            ('sale_order_id', '=', self.sale_order.id),
            ('customer_id', '=', self.customer.id),
            ('product_id', '=', self.warranty_product.id),
        ])
        self.assertTrue(claim)
