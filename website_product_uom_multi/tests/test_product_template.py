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

from odoo.addons.website_product_uom_multi.models import (
    product_template as product_template_module,
)


class FakeRequest:

    def __init__(self, env):
        self.env = env
        self.session = {}


@tagged('post_install', '-at_install')
class TestProductTemplate(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.uom_pack_6 = cls.env.ref('uom.product_uom_pack_6')
        cls.product = cls.env['product.product'].create({
            'name': 'Website UoM Contextual Price Product',
            'type': 'consu',
            'list_price': 10.0,
            'uom_id': cls.uom_unit.id,
        })

    def test_get_contextual_price_uses_uom_from_session(self):
        fake_request = FakeRequest(self.env)
        fake_request.session['uom_id'] = self.uom_pack_6.id
        product_template = self.product.product_tmpl_id

        with patch.object(product_template_module, 'request', fake_request):
            session_uom_price = product_template._get_contextual_price(self.product)

        context_uom_price = product_template.with_context(
            uom=self.uom_pack_6.id
        )._get_contextual_price(self.product)

        self.assertEqual(session_uom_price, context_uom_price)
