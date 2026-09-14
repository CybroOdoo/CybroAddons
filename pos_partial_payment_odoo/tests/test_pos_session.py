from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.common import TestPoSCommon


@tagged('-at_install', 'post_install')
class TestPosSession(TestPoSCommon):

    def setUp(self):
        super().setUp()
        self.config = self.basic_config
        self.session = self.open_new_session()

    def test_loader_params_res_partner_adds_prevent_partial_payment(self):
        result = self.session._loader_params_res_partner()

        self.assertIn(
            'prevent_partial_payment',
            result['search_params']['fields'],
        )
