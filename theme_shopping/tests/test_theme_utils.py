from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestThemeUtils(TransactionCase):
    def test_theme_configures_shop_options(self):
        website = self.env['website'].search([], limit=1)
        website = website.with_context(website_id=website.id)
        utils = self.env['theme.utils'].with_context(website_id=website.id)
        utils._theme_shopping_post_copy(self.env['ir.module.module'].search([
            ('name', '=', 'theme_shopping'),
        ]))
        for xml_id in (
            'website_sale.products_categories',
            'website_sale.product_comment',
            'website_sale.option_collapse_products_categories',
            'website_sale.product_buy_now',
        ):
            self.assertTrue(website.is_view_active(xml_id), xml_id)
        for xml_id in (
            'website_sale.products_categories_top',
            'website_sale.add_to_compare',
        ):
            self.assertFalse(website.is_view_active(xml_id), xml_id)
