from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestTopDeal(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.template'].create(
            {
                'name': 'Top deal test product',
                'list_price': 100,
            },
        )

    def test_enabling_deal_preserves_regular_price(self):
        self.product.write({'is_top_deal_product': True})

        self.assertEqual(self.product.actual_price, 100)
        self.assertEqual(self.product.list_price, 100)

    def test_active_deal_applies_offer_price(self):
        self.product.write(
            {
                'is_top_deal_product': True,
                'offer_price': 80,
                'time_period_from': fields.Date.today(),
                'time_period_end': fields.Date.today(),
            },
        )

        self.product.check_top_deal()

        self.assertTrue(self.product.ready_to_top_deal)
        self.assertEqual(self.product.list_price, 80)
        self.assertEqual(self.product.compare_list_price, 100)

    def test_disabling_deal_restores_regular_price(self):
        self.product.write(
            {
                'is_top_deal_product': True,
                'offer_price': 80,
                'time_period_from': fields.Date.today(),
                'time_period_end': fields.Date.today(),
            },
        )
        self.product.check_top_deal()

        self.product.write({'is_top_deal_product': False})

        self.assertEqual(self.product.list_price, 100)
        self.assertEqual(self.product.compare_list_price, 0)
        self.assertFalse(self.product.ready_to_top_deal)

    def test_future_deal_restores_regular_price(self):
        tomorrow = fields.Date.add(fields.Date.today(), days=1)
        self.product.write(
            {
                'is_top_deal_product': True,
                'offer_price': 80,
                'time_period_from': tomorrow,
                'time_period_end': fields.Date.add(tomorrow, days=1),
            },
        )

        self.product.check_top_deal()

        self.assertFalse(self.product.ready_to_top_deal)
        self.assertEqual(self.product.list_price, 100)
        self.assertEqual(self.product.compare_list_price, 0)

    def test_deal_period_must_be_valid(self):
        with self.assertRaises(ValidationError):
            self.product.write(
                {
                    'is_top_deal_product': True,
                    'time_period_from': fields.Date.add(fields.Date.today(), days=1),
                    'time_period_end': fields.Date.today(),
                },
            )

    def test_expired_deal_restores_regular_price(self):
        self.product.write({'is_top_deal_product': True, 'offer_price': 80})
        self.product.check_top_deal()
        self.assertEqual(self.product.list_price, 80)
        yesterday = fields.Date.subtract(fields.Date.today(), days=1)
        self.product.write({
            'time_period_from': yesterday,
            'time_period_end': yesterday,
        })
        self.product.check_top_deal()
        self.assertFalse(self.product.ready_to_top_deal)
        self.assertEqual(self.product.list_price, 100)
        self.assertEqual(self.product.compare_list_price, 0)

    def test_created_deal_saves_regular_price(self):
        product = self.env['product.template'].create({
            'name': 'Created as deal',
            'list_price': 120,
            'is_top_deal_product': True,
            'offer_price': 90,
        })
        product.apply_top_deal_time()
        self.assertEqual(product.actual_price, 120)
        self.assertEqual(product.list_price, 90)
        self.assertTrue(product.ready_to_top_deal)

    def test_offer_cannot_increase_regular_price(self):
        self.product.write({'is_top_deal_product': True, 'offer_price': 150})
        self.env['product.template'].check_top_deal()
        self.assertEqual(self.product.list_price, 100)
        self.assertEqual(self.product.compare_list_price, 0)
        self.assertTrue(self.product.ready_to_top_deal)

    def test_mixed_recordset_preserves_each_regular_price(self):
        other = self.product.copy({'list_price': 200})
        self.product.write({'is_top_deal_product': True})
        products = self.product | other
        products.write({'is_top_deal_product': True, 'offer_price': 50})
        products.check_top_deal()
        self.assertEqual(self.product.actual_price, 100)
        self.assertEqual(other.actual_price, 200)
        products.write({'is_top_deal_product': False})
        self.assertEqual(self.product.list_price, 100)
        self.assertEqual(other.list_price, 200)

    def test_onchange_restores_regular_price(self):
        product = self.env['product.template'].new({'list_price': 100})
        product.is_top_deal_product = True
        product._onchange_is_top_deal_product()
        self.assertEqual(product.actual_price, 100)
        self.assertEqual(product.time_period_from, fields.Date.today())
        self.assertEqual(product.time_period_end, fields.Date.today())
        product.list_price = 80
        product.ready_to_top_deal = True
        product.is_top_deal_product = False
        product._onchange_is_top_deal_product()
        self.assertEqual(product.list_price, 100)
        self.assertFalse(product.ready_to_top_deal)

    def test_combination_includes_offer_price(self):
        self.product.offer_price = 80
        website = self.env['website'].search([], limit=1)
        info = self.product.with_context(website_id=website.id)._get_combination_info(
            pricelist=self.env['product.pricelist'].search([], limit=1),
            fiscal_position=self.env['account.fiscal.position'],
        )
        self.assertEqual(info['offer_price'], 80)
