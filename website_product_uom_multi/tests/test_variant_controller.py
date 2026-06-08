# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.info)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.website_product_uom_multi.controllers import (
    variant as variant_controller_module,
)


class FakeRequest:

    def __init__(self, env):
        self.env = env
        self.session = {}


@tagged('post_install', '-at_install')
class TestVariantController(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.uom_pack_6 = cls.env.ref('uom.product_uom_pack_6')
        cls.product = cls.env['product.product'].create({
            'name': 'Website UoM Variant Product',
            'type': 'consu',
            'list_price': 10.0,
            'uom_id': cls.uom_unit.id,
        })

    def test_get_combination_info_scales_prices_for_selected_uom(self):
        controller = variant_controller_module.Vairant()
        fake_request = FakeRequest(self.env)

        with patch.object(variant_controller_module, 'request', fake_request):
            with patch.object(
                variant_controller_module.WebsiteSaleVariantController,
                'get_combination_info_website',
                return_value={'price': 10.0, 'list_price': 12.0},
            ):
                result = type(controller).get_combination_info_website.__wrapped__(
                    controller,
                    product_template_id=self.product.product_tmpl_id.id,
                    product_id=self.product.id,
                    combination=[],
                    add_qty=1,
                    uom=self.uom_pack_6.id,
                )

        self.assertEqual(fake_request.session['uom_id'], self.uom_pack_6.id)
        self.assertEqual(result['price'], 60.0)
        self.assertEqual(result['list_price'], 72.0)
