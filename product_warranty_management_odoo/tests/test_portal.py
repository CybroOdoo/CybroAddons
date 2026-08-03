from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.base.tests.common import HttpCaseWithUserPortal


@tagged('post_install', '-at_install')
class TestWarrantyPortal(HttpCaseWithUserPortal):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_portal.password = 'portal'
        cls.product = cls.env['product.product'].create({
            'name': 'Portal Warranty Product',
            'type': 'consu',
            'is_warranty_available': True,
            'warranty_duration': 6,
            'taxes_id': [Command.clear()],
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner_portal.id,
            'is_warranty_check': True,
            'order_line': [
                Command.create({
                    'product_id': cls.product.id,
                    'product_uom_qty': 1.0,
                }),
            ],
        })
        cls.claim = cls.env['warranty.claim'].create({
            'customer_id': cls.partner_portal.id,
            'sale_order_id': cls.sale_order.id,
            'product_id': cls.product.id,
        })

    def test_portal_home_displays_claim_counter(self):
        self.authenticate('portal', 'portal')

        response = self.url_open('/my')

        self.assertEqual(response.status_code, 403)
        self.assertIn('Warranty Claim', response.text)

    def test_my_claims_route_displays_claim_data(self):
        self.authenticate('portal', 'portal')

        response = self.url_open('/my/claims')

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.partner_portal.name, response.text)
        self.assertIn(self.sale_order.name, response.text)
        self.assertIn(self.product.name, response.text)
