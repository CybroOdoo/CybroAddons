# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

from odoo.tests import TransactionCase, tagged

@tagged('post_install', '-at_install')
class TestFleetSubServiceType(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

    def test_fleet_sub_service_type_onchange(self):
        """Test _onchange_service_type_id in fleet.sub.service.type"""
        service_type = self.env['fleet.service.type'].create({
            'name': 'Oil Change',
            'category': 'contract',
        })
        
        sub_service = self.env['fleet.sub.service.type'].new({
            'service_type_id': service_type.id,
        })
        
        sub_service._onchange_service_type_id()
        self.assertEqual(sub_service.service_category, 'contract')
