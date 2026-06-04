from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPoSConfig(TransactionCase):

    def test_limited_products_loading_defaults_to_enabled(self):
        config = self.env['pos.config'].create({
            'name': 'Limited Product Loading Config',
        })

        self.assertTrue(config.limited_products_loading)
