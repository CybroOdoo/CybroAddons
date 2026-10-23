#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import TransactionCase


class FreightCommon(TransactionCase):
    """Shared data for the freight tests"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_shipper = cls.env['res.partner'].create(
            {'name': 'Test Shipper', 'email': 'shipper@test.com'})
        cls.partner_agent = cls.env['res.partner'].create(
            {'name': 'Test Agent', 'email': 'agent@test.com'})
        cls.port_loading = cls.env['freight.port'].create({
            'name': 'Loading Port',
            'country_id': cls.env.ref('base.us').id,
            'water': True,
        })
        cls.port_discharging = cls.env['freight.port'].create({
            'name': 'Discharging Port',
            'country_id': cls.env.ref('base.be').id,
            'water': True,
        })
        cls.container = cls.env['freight.container'].create({
            'name': 'Test Container',
            'size': 20,
            'weight': 1000,
            'volume': 500,
        })
        cls.pricing = cls.env['freight.price'].create({
            'name': 'Standard Pricing',
            'weight': 10,
            'volume': 20,
        })
        cls.product = cls.env['product.product'].create(
            {'name': 'Test Goods'})
        cls.freight_user = cls.env['res.users'].create({
            'name': 'Freight User',
            'login': 'freight_user_test',
            'email': 'freight.user@test.com',
            'group_ids': [(6, 0, [
                cls.env.ref('freight_management_system.group_freight_user').id,
            ])],
        })

    @classmethod
    def _create_order(cls, env=None, **kwargs):
        vals = {
            'shipper_id': cls.partner_shipper.id,
            'type': 'export',
            'transport_type': 'water',
            'loading_port_id': cls.port_loading.id,
            'discharging_port_id': cls.port_discharging.id,
            'agent_id': cls.partner_agent.id,
        }
        vals.update(kwargs)
        return (env or cls.env)['freight.order'].create(vals)

    def _add_line(self, order, **kwargs):
        vals = {
            'order_id': order.id,
            'container_id': self.container.id,
            'product_id': self.product.id,
            'billing_type': 'weight',
            'pricing_id': self.pricing.id,
            'weight': 100,
        }
        vals.update(kwargs)
        return self.env['freight.order.line'].create(vals)
