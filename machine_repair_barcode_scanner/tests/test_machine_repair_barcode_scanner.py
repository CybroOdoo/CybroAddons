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
from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged('post_install', '-at_install')
class TestMachineRepairBarcodeScanner(HttpCase):
    """Test cases for the barcode search controller."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Grant admin the Repair Manager group from the dependency module
        # so the controller can write to machine.repair records.
        repair_manager_group = cls.env.ref(
            'base_machine_repair_management.repair_manager_access')
        cls.env.ref('base.user_admin').write({
            'group_ids': [Command.link(repair_manager_group.id)]
        })
        cls.machine = cls.env['product.product'].create({
            'name': 'Controller Machine',
            'barcode': '2198765432101',
            'is_machine': True,
        })
        cls.part = cls.env['product.product'].create({
            'name': 'Controller Part',
            'barcode': '2198765432102',
            'is_machine_parts': True,
        })
        cls.plain_product = cls.env['product.product'].create({
            'name': 'Plain Product',
            'barcode': '2198765432103',
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

    def setUp(self):
        super().setUp()
        admin = self.env.ref('base.user_admin')
        with patch(
            'odoo.addons.base.models.res_users.ResUsers._login',
            return_value={'uid': admin.id, 'auth_method': 'password'},
        ):
            self.authenticate('admin', 'any')

    def _scan(self, code, product_type):
        """Call the barcode route and return the JSON-RPC result."""
        payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {
                'last_code': code,
                'order_id': self.repair_order.id,
                'product': product_type,
            },
        }
        response = self.url_open(
            '/barcode_search/machine',
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'},
        )
        self.assertEqual(response.status_code, 200)
        return response.json().get('result')

    def test_scan_machine(self):
        """Scanning a machine barcode sets the machine on the order."""
        self.assertIs(self._scan(self.machine.barcode, 'machine'), True)
        self.repair_order.invalidate_recordset()
        self.assertEqual(self.repair_order.machine_id, self.machine)
        self.assertEqual(
            self.repair_order.machine_categ_id, self.machine.categ_id)

    def test_scan_unknown_barcode(self):
        """An unknown barcode returns False."""
        self.assertIs(self._scan('0000000000000', 'machine'), False)

    def test_scan_not_machine(self):
        """A product that is not a machine is rejected as a machine."""
        self.assertEqual(
            self._scan(self.plain_product.barcode, 'machine'), 'not_machine')
        self.repair_order.invalidate_recordset()
        self.assertFalse(self.repair_order.machine_id)

    def test_scan_part_adds_and_increments(self):
        """Scanning a part adds a line, scanning again adds one to the qty."""
        self.assertIs(self._scan(self.part.barcode, 'parts'), True)
        self.repair_order.invalidate_recordset()
        self.assertEqual(len(self.repair_order.consume_part_ids), 1)
        self.assertEqual(self.repair_order.consume_part_ids.qty, 1)
        self.assertIs(self._scan(self.part.barcode, 'parts'), True)
        self.repair_order.invalidate_recordset()
        self.assertEqual(len(self.repair_order.consume_part_ids), 1)
        self.assertEqual(self.repair_order.consume_part_ids.qty, 2)

    def test_scan_not_part(self):
        """A product that is not a machine part is rejected as a part."""
        self.assertEqual(
            self._scan(self.plain_product.barcode, 'parts'), 'not_part')
        self.repair_order.invalidate_recordset()
        self.assertFalse(self.repair_order.consume_part_ids)
