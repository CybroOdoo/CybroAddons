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
from datetime import datetime
from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.website_product_uom_multi.controllers import (
    product_configurator as product_configurator_module,
)


class FakeRequest:

    def __init__(self, env):
        self.env = env
        self.session = {}
        self.context_updates = []

    def update_context(self, **kwargs):
        self.context_updates.append(kwargs)


@tagged('post_install', '-at_install')
class TestProductConfiguratorController(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.uom_pack_6 = cls.env.ref('uom.product_uom_pack_6')
        cls.product = cls.env['product.product'].create({
            'name': 'Website UoM Configurator Product',
            'type': 'consu',
            'list_price': 10.0,
            'uom_id': cls.uom_unit.id,
        })

    def test_get_values_passes_product_uom_to_product_information(self):
        controller = product_configurator_module.SaleProductConfiguratorController()
        fake_request = FakeRequest(self.env)

        with patch.object(product_configurator_module, 'request', fake_request):
            with patch.object(
                controller, '_get_product_template', return_value=self.product.product_tmpl_id
            ):
                with patch.object(
                    controller, '_get_product_information',
                    return_value={'product_id': self.product.id},
                ) as product_information:
                    result = (
                        type(controller)
                        .sale_product_configurator_get_values
                        .__wrapped__(
                            controller,
                            product_template_id=self.product.product_tmpl_id.id,
                            quantity=2,
                            currency_id=self.env.company.currency_id.id,
                            so_date=datetime.today().isoformat(),
                            product_uom_id=self.uom_pack_6.id,
                            pricelist_id=self.env['product.pricelist'].search([], limit=1).id,
                            only_main_product=True,
                        )
                    )

        self.assertEqual(result['products'], [{'product_id': self.product.id}])
        self.assertEqual(result['optional_products'], [])
        self.assertEqual(result['currency_id'], self.env.company.currency_id.id)
        self.assertEqual(
            product_information.call_args.kwargs['product_uom_id'],
            self.uom_pack_6.id,
        )
