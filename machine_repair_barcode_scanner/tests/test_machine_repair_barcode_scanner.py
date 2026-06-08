# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aleena K (odoo@cybrosys.com)
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

import json
from unittest.mock import patch

from odoo.fields import Command
from odoo.tests.common import HttpCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestMachineRepairBarcodeScanner(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Grant admin the Repair Manager group from the dependency module
        # so the controller can write to machine.repair records
        repair_manager_group = cls.env.ref(
            'base_machine_repair_management.repair_manager_access'
        )
        cls.env.ref('base.user_admin').write({
            'group_ids': [Command.link(repair_manager_group.id)]
        })

        cls.product = cls.env['product.product'].create({
            'name': 'Controller Machine',
            'barcode': '2198765432101',
        })

        cls.customer = cls.env['res.partner'].create({
            'name': 'Controller Customer',
        })

        cls.repair_order = cls.env['machine.repair'].create({
            'name': 'Controller Repair',
            'repair_seq': 'MRP/002',
            'customer_id': cls.customer.id,
            'priority': 'low',
            'repair_detail': 'Controller repair testing',
        })

    def test_barcode_controller_route(self):
        """Test barcode controller route."""

        admin = self.env.ref('base.user_admin')

        with patch(
            'odoo.addons.base.models.res_users.ResUsers._login',
            return_value={
                'uid': admin.id,
                'auth_method': 'password',
            }
        ):
            self.authenticate('admin', 'any')

        payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {
                'last_code': '2198765432101',
                'order_id': self.repair_order.id,
                'product': 'machine',
            }
        }

        response = self.url_open(
            '/barcode_search/machine',
            data=json.dumps(payload),
            headers={
                'Content-Type': 'application/json',
            }
        )

        self.assertEqual(response.status_code, 200)

        result = response.json()
        self.assertTrue(result.get('result'))

        self.repair_order.invalidate_recordset()
        self.assertEqual(self.repair_order.machine_id, self.product)