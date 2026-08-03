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

class TestFreightTracking(common.TransactionCase):

    def setUp(self):
        super(TestFreightTracking, self).setUp()
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

    def test_01_tracking_submission(self):
        """Test tracking submission and record creation"""
        tracking_wizard = self.env['freight.order.track'].create({
            'freight_id': self.order.id,
            'source_loc_id': self.port_loading.id,
            'destination_loc_id': self.port_discharging.id,
            'transport_type': 'water',
            'type': 'received',
        })
        
        tracking_wizard.action_order_submit()
        
        # Check if freight.track record is created
        track_record = self.env['freight.track'].search([('freight_id', '=', self.order.id)])
        self.assertTrue(track_record, "Freight track record should be created")
        self.assertEqual(track_record.type, 'received')
        self.assertEqual(track_record.source_loc_id, self.port_loading)
        self.assertEqual(track_record.destination_loc_id, self.port_discharging)
