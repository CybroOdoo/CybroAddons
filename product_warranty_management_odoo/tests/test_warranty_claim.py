from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestWarrantyClaim(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({'name': 'Warranty Customer'})
        cls.product = cls.env['product.product'].create({
            'name': 'Claim Product',
            'type': 'consu',
            'is_warranty_available': True,
            'warranty_expiry': '2026-12-31',
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.customer.id,
        })

    def test_change_status_approved(self):
        claim = self.env['warranty.claim'].create({
            'customer_id': self.customer.id,
            'sale_order_id': self.sale_order.id,
            'product_id': self.product.id,
        })

        claim.change_status_approved()

        self.assertEqual(claim.state, 'approved')

    def test_change_status_rejected(self):
        claim = self.env['warranty.claim'].create({
            'customer_id': self.customer.id,
            'sale_order_id': self.sale_order.id,
            'product_id': self.product.id,
        })

        claim.change_status_rejected()

        self.assertEqual(claim.state, 'rejected')

    def test_related_product_expiry_date_and_default_user(self):
        claim = self.env['warranty.claim'].create({
            'customer_id': self.customer.id,
            'sale_order_id': self.sale_order.id,
            'product_id': self.product.id,
        })

        self.assertEqual(claim.partner_id, self.env.user)
        self.assertEqual(str(claim.product_expiry_date), '2026-12-31')
