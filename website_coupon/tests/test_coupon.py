from datetime import datetime, timedelta

from odoo.tests.common import TransactionCase, at_install, post_install


@at_install(False)
@post_install(True)
class CouponTC(TransactionCase):

    def setUp(self):
        super(CouponTC, self).setUp()
        self.voucher = self.env['gift.voucher'].create(self.base_voucher_vals)
        self.coupon = self.env['gift.coupon'].create(self.base_coupon_vals)
        self.partner1 = self.env.ref('base.res_partner_1')
        self.partner2 = self.env.ref('base.res_partner_2')

    @property
    def base_voucher_vals(self):
        return {
            'name': 'test voucher',
            'voucher_type': 'all',
            'min_value': 0.,
            'max_value': 100000.,
            'expiry_date': '2100-01-01',
            'product_id': False,
            'product_categ': False,
        }

    @property
    def base_coupon_vals(self):
        return {
            'name': 'test coupon',
            'code': 'TEST_CODE',
            'total_avail': '1000',
            'voucher_val': 10,
            'type': 'fixed',
            'voucher': self.voucher.id,
            'partner_id': False,
            'limit': 0,  # means no limit
            'start_date': False,
            'end_date': False,
        }

    def reset_coupon(self):
        self.voucher.update(self.base_voucher_vals)
        self.coupon.update(self.base_coupon_vals)
        self.env['partner.coupon'].sudo().search([
            ('coupon', '=', self.coupon.code),
        ]).unlink()
        assert self.coupon.is_valid(self.partner1)
        assert self.coupon.is_valid(self.partner2)

    def test_use_coupon(self):
        self.reset_coupon()

        self.coupon.use_coupon(self.partner1, 10)
        self.assertEqual(self.coupon.total_avail, 990)
        self.coupon.use_coupon(self.partner1, 20)
        self.assertEqual(self.coupon.total_avail, 970)
        self.assertEqual(self.coupon.applied_coupons(self.partner1).number, 30)

        self.coupon.use_coupon(self.partner2, 50)
        self.assertEqual(self.coupon.total_avail, 920)
        self.assertEqual(self.coupon.applied_coupons(self.partner2).number, 50)

    def test_is_valid(self):
        partner1 = self.partner1
        partner2 = self.partner2
        coupon = self.coupon

        self.reset_coupon()

        # Check partner field behaviour
        coupon.partner_id = partner1.id
        self.assertFalse(coupon.is_valid(partner2))
        self.assertTrue(coupon.is_valid(partner1))

        # Check total_avail + partner.coupon behaviour
        coupon.total_avail = 0
        self.assertFalse(coupon.is_valid(partner2))

        self.reset_coupon()

        coupon.partner_id = partner2.id
        coupon.use_coupon(partner2, 999)
        self.assertTrue(coupon.is_valid(partner2))
        coupon.use_coupon(partner2, 1)
        self.assertFalse(coupon.is_valid(partner2))

        self.reset_coupon()

        # Check per-partner limit behaviour
        coupon.limit = 10
        coupon.use_coupon(partner2, 9)
        self.assertTrue(coupon.is_valid(partner2))
        coupon.use_coupon(partner2, 1)
        self.assertFalse(coupon.is_valid(partner2))

        self.reset_coupon()

        # Check time limits
        today = datetime.now().date()
        coupon.start_date = today + timedelta(days=1)
        self.assertFalse(coupon.is_valid(partner2))

        self.reset_coupon()

        coupon.end_date = today - timedelta(days=1)
        self.assertFalse(coupon.is_valid(partner2))

        coupon.start_date = today - timedelta(days=10)
        coupon.end_date = today - timedelta(days=2)
        self.assertFalse(coupon.is_valid(partner2))

        coupon.start_date = today - timedelta(days=1)
        coupon.end_date = today + timedelta(days=1)
        self.assertTrue(coupon.is_valid(partner2))

    def test_consume_coupon(self):
        order = self.env['sale.order'].create({'partner_id': self.partner2.id})
        categ = self.env['product.category'].create({'name': 'test categ 1'})
        product1 = self.env['product.product'].create({
            'name': 'test product 1',
            'list_price': 100.,
            'categ_id': categ.id,
        })
        product2 = self.env['product.product'].create({
            'name': 'test product 2',
            'list_price': 300.,
        })
        product3 = self.env['product.product'].create({
            'name': 'test product 3',
            'list_price': 200.,
            'categ_id': categ.id,
        })
        self.env['sale.order.line'].create({
            'name': 'test line 1',
            'product_id': product1.id,
            'product_uom_qty': 10,
            'order_id': order.id,
            'product_uom': product1.uom_id.id,
            'price_unit': 120.,
            })
        self.env['sale.order.line'].create({
            'name': 'test line 2',
            'product_id': product2.id,
            'product_uom_qty': 5,
            'order_id': order.id,
            'product_uom': product2.uom_id.id,
            'price_unit': 360.,
            })
        self.env['sale.order.line'].create({
            'name': 'test line 3',
            'product_id': product3.id,
            'product_uom_qty': 20,
            'order_id': order.id,
            'product_uom': product3.uom_id.id,
            'price_unit': 240.,
            })

        used, amount = self.coupon.consume_coupon(order)
        self.assertEqual((used, amount), (35, 350))

        self.reset_coupon()

        self.coupon.type = 'percentage'
        self.coupon.voucher_val = 10
        used, amount = self.coupon.consume_coupon(order)
        self.assertEqual((used, amount), (35, 10*10+5*30+20*20))

        self.reset_coupon()

        self.coupon.type = 'percentage'
        self.coupon.voucher_val = 10
        self.voucher.voucher_type = 'product'
        self.voucher.product_id = product2.id
        used, amount = self.coupon.consume_coupon(order)
        self.assertEqual((used, amount), (5, 5*30))

        self.reset_coupon()

        self.coupon.type = 'percentage'
        self.coupon.voucher_val = 10
        self.voucher.voucher_type = 'category'
        self.voucher.product_categ = categ.id
        used, amount = self.coupon.consume_coupon(order)
        self.assertEqual((used, amount), (10+20, 10*10+20*20))

        self.reset_coupon()

        self.coupon.type = 'percentage'
        self.coupon.voucher_val = 10
        self.coupon.total_avail = 7
        used, amount = self.coupon.consume_coupon(order)
