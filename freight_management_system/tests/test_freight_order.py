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
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged

from .common import FreightCommon


@tagged('post_install', '-at_install')
class TestFreightOrder(FreightCommon):

    def _confirmed_order(self, env=None, **line_kwargs):
        order = self._create_order(env=env)
        self._add_line(order, **line_kwargs)
        order.action_submit()
        order.action_create_custom_clearance()
        order.clearance_ids.action_confirm()
        order.action_confirm()
        return order

    def test_01_freight_order_flow(self):
        """Test the basic flow of a freight order"""
        order = self._create_order()
        self.assertEqual(order.state, 'draft')
        line = self._add_line(order)
        self.assertEqual(line.price, 10)
        self.assertEqual(line.total_price, 1000)
        self.assertEqual(order.total_order_price, 1000)

        order.action_submit()
        self.assertEqual(order.state, 'submit')

        cc_action = order.action_create_custom_clearance()
        self.assertEqual(cc_action.get('name'), 'Custom Clearance')
        self.assertTrue(order.clearance)
        self.assertEqual(order.clearance_count, 1)
        self.assertEqual(order.clearance_ids.name, 'CC - ' + order.name)
        with self.assertRaises(ValidationError):
            order.action_create_custom_clearance()
        # The clearance is still in draft
        with self.assertRaises(ValidationError):
            order.action_confirm()
        self.assertEqual(order.state, 'submit')
        self.assertEqual(self.container.state, 'available')

        order.clearance_ids.action_confirm()
        order.action_confirm()
        self.assertEqual(order.state, 'confirm')
        self.assertEqual(self.container.state, 'reserve')

        inv_action = order.action_create_invoice()
        self.assertEqual(inv_action.get('name'), 'Customer Invoice')
        self.assertEqual(order.state, 'invoice')
        self.assertEqual(order.invoice_count, 1)
        invoice = order.invoice_ids
        self.assertEqual(invoice.freight_order_id, order)
        self.assertEqual(order.get_invoice()['domain'],
                         [('freight_order_id', '=', order.id)])
        inv_line = invoice.invoice_line_ids
        self.assertEqual(inv_line.quantity, 100)
        self.assertEqual(inv_line.price_unit, 10)
        self.assertEqual(inv_line.product_id, self.product)

        order.action_done()
        self.assertEqual(order.state, 'done')
        self.assertEqual(self.container.state, 'available')

    def test_02_order_line_constraints(self):
        """Test weight and volume constraints on order lines"""
        order = self._create_order()
        with self.assertRaises(ValidationError):
            self._add_line(order, weight=2000)
        with self.assertRaises(ValidationError):
            self._add_line(order, billing_type='volume', weight=0,
                           volume=600)
        # Changing the container or the billing type is checked too
        line = self._add_line(order, weight=800)
        small = self.env['freight.container'].create({
            'name': 'Small', 'size': 1, 'weight': 100, 'volume': 10})
        with self.assertRaises(ValidationError):
            line.container_id = small

    def test_03_name_and_states(self):
        """Names are only generated when not given, states are validated"""
        order = self._create_order(name='Given name')
        self.assertEqual(order.name, 'Given name')
        order = self._create_order()
        self.assertTrue(order.name.startswith('FO-'))
        with self.assertRaises(ValidationError):
            order.action_confirm()
        with self.assertRaises(ValidationError):
            order.action_done()
        with self.assertRaises(ValidationError):
            order.action_create_invoice()
        order.action_submit()
        with self.assertRaises(ValidationError):
            order.action_submit()
        # No clearance at all
        with self.assertRaises(ValidationError):
            order.action_confirm()
        order.action_cancel()
        self.assertEqual(order.state, 'cancel')
        with self.assertRaises(ValidationError):
            order.action_cancel()

    def test_04_invoice_rules(self):
        """No duplicate invoice, no billing of empty quantities"""
        order = self._confirmed_order(weight=0)
        with self.assertRaises(ValidationError):
            order.action_create_invoice()
        order.service_ids = [(0, 0, {
            'service_id': self.env['freight.service'].create(
                {'name': 'Handling', 'sale_price': 5}).id,
            'qty': 2,
        })]
        order.route_ids = [(0, 0, {
            'routes_id': self.env.ref(
                'freight_management_system.main_carriage').id,
            'transport_type': 'water',
        })]
        order.action_create_invoice()
        lines = order.invoice_ids.invoice_line_ids
        # The empty cargo line is skipped
        self.assertEqual(lines.mapped('name'), ['Main Carriage', 'Handling'])
        self.assertEqual(lines.filtered(
            lambda line: line.name == 'Handling').quantity, 2)
        with self.assertRaises(ValidationError):
            order.action_create_invoice()

    def test_05_cancel(self):
        """Cancelling releases containers but respects invoices"""
        order = self._confirmed_order()
        self.assertEqual(self.container.state, 'reserve')
        order.action_create_invoice()
        with self.assertRaises(ValidationError):
            order.action_cancel()
        order.invoice_ids.button_cancel()
        order.action_cancel()
        self.assertEqual(order.state, 'cancel')
        self.assertEqual(self.container.state, 'available')

    def test_06_freight_user_flow(self):
        """A user holding only the freight group can run the whole flow"""
        user_env = self.env(user=self.freight_user)
        self.assertFalse(
            self.freight_user.has_group('account.group_account_manager'))
        order = self._confirmed_order(env=user_env)
        # The counts are computed without accounting access error
        self.assertEqual(order.clearance_count, 1)
        self.assertEqual(order.invoice_count, 0)
        order.action_create_invoice()
        self.assertEqual(order.invoice_count, 1)
        order.action_done()
        self.assertEqual(order.state, 'done')
        self.assertEqual(self.container.state, 'available')
        # Master data is read-only for the freight user
        port = user_env['freight.port'].browse(self.port_loading.id)
        self.assertEqual(port.name, 'Loading Port')
        with self.assertRaises(AccessError):
            port.write({'name': 'Changed'})
        with self.assertRaises(AccessError):
            user_env['freight.container'].create({
                'name': 'X', 'size': 1, 'weight': 1, 'volume': 1})

    def test_07_freight_manager(self):
        """The manager maintains the master data"""
        manager = self.env['res.users'].create({
            'name': 'Freight Manager',
            'login': 'freight_manager_test',
            'group_ids': [(6, 0, [
                self.env.ref('freight_management_system.group_freight').id])],
        })
        self.assertTrue(manager.has_group(
            'freight_management_system.group_freight_user'))
        port = self.port_loading.with_user(manager)
        port.write({'name': 'Changed'})
        self.assertEqual(port.name, 'Changed')
