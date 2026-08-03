# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Prathyunnan R (odoo@cybrosys.com)
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
from odoo.tests import common

class TestCustomClearance(common.TransactionCase):

    def setUp(self):
        super(TestCustomClearance, self).setUp()
        self.partner_shipper = self.env['res.partner'].create({'name': 'Test Shipper', 'email': 'shipper@test.com'})
        self.partner_agent = self.env['res.partner'].create({'name': 'Test Agent', 'email': 'agent@test.com'})
        self.port_loading = self.env['freight.port'].create({'name': 'Loading Port', 'country_id': self.env.ref('base.us').id})
        self.port_discharging = self.env['freight.port'].create({'name': 'Discharging Port', 'country_id': self.env.ref('base.be').id})

        self.order = self.env['freight.order'].create({
            'shipper_id': self.partner_shipper.id,
            'type': 'export',
            'transport_type': 'water',
            'loading_port_id': self.port_loading.id,
            'discharging_port_id': self.port_discharging.id,
            'agent_id': self.partner_agent.id,
        })

    def test_01_custom_clearance_actions(self):
        """Test custom clearance actions"""
        clearance = self.env['custom.clearance'].create({
            'freight_id': self.order.id,
            'agent_id': self.partner_agent.id,
        })
        
        # Test compute name
        clearance._compute_name()
        self.assertEqual(clearance.name, 'CC - ' + self.order.name)

        # Test onchange
        clearance._onchange_freight_id()
        self.assertEqual(clearance.loading_port_id, self.port_loading)
        self.assertEqual(clearance.discharging_port_id, self.port_discharging)

        # Test confirm
        clearance.action_confirm()
        self.assertEqual(clearance.state, 'confirm', "Clearance should be confirmed")

        # Test revision (wizard)
        action = clearance.action_revision()
        self.assertEqual(action['res_model'], 'custom.clearance.revision')
        self.assertEqual(action['context']['default_custom_id'], clearance.id)
