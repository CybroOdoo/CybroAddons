#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestRoleRecordRules(TransactionCase):
    """Drivers only reach their own work; unrelated internal users get no WM data."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users']
        driver_groups = [(6, 0, [
            cls.env.ref('base.group_user').id,
            cls.env.ref('wm_base.group_wm_driver').id,
        ])]
        cls.customer = cls.env['res.partner'].create({'name': 'Rule Customer'})
        cls.driver_a_partner = cls.env['res.partner'].create({'name': 'Rule Driver A'})
        cls.driver_b_partner = cls.env['res.partner'].create({'name': 'Rule Driver B'})
        cls.driver_a = Users.create({
            'name': 'Rule Driver A', 'login': 'rule_driver_a',
            'partner_id': cls.driver_a_partner.id, 'group_ids': driver_groups})
        cls.driver_b = Users.create({
            'name': 'Rule Driver B', 'login': 'rule_driver_b',
            'partner_id': cls.driver_b_partner.id, 'group_ids': driver_groups})
        cls.dispatcher = Users.create({
            'name': 'Rule Dispatcher', 'login': 'rule_dispatcher',
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('wm_base.group_wm_dispatcher').id])]})
        cls.plain_user = Users.create({
            'name': 'Rule Plain User', 'login': 'rule_plain_user',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])]})
        cls.category = cls.env['wm.waste.category'].create({'name': 'Rule Cat', 'code': 'RULECAT'})
        cls.point = cls.env['wm.collection.point'].create({
            'name': 'Rule Point', 'partner_id': cls.customer.id,
            'category_ids': [(6, 0, cls.category.ids)]})
        cls.order_a = cls._make_order(cls.driver_a_partner)
        cls.order_b = cls._make_order(cls.driver_b_partner)
        Log = cls.env['wm.collection.order.status.log']
        cls.log_a = Log.create({'order_id': cls.order_a.id, 'status': 'en_route', 'driver_id': cls.driver_a.id})
        cls.log_b = Log.create({'order_id': cls.order_b.id, 'status': 'en_route', 'driver_id': cls.driver_b.id})

    @classmethod
    def _make_order(cls, driver_partner):
        route = cls.env['wm.route'].create({'name': 'Rule Route %s' % driver_partner.name, 'driver_id': driver_partner.id})
        order = cls.env['wm.collection.order'].create({
            'partner_id': cls.customer.id,
            'collection_point_id': cls.point.id,
            'route_id': route.id,
            'state': 'dispatched',
        })
        cls.env['wm.collection.order.line'].create({
            'order_id': order.id, 'category_id': cls.category.id, 'estimated_weight': 5.0})
        return order

    def test_driver_sees_only_own_orders_and_logs(self):
        logs = self.env['wm.collection.order.status.log'].with_user(self.driver_a)
        self.assertEqual(logs.search([('id', 'in', (self.log_a | self.log_b).ids)]), self.log_a)
        orders = self.env['wm.collection.order'].with_user(self.driver_a)
        self.assertEqual(orders.search([('id', 'in', (self.order_a | self.order_b).ids)]), self.order_a)

    def test_driver_cannot_edit_another_drivers_log(self):
        with self.assertRaises(AccessError):
            self.log_b.with_user(self.driver_a).write({'note': 'tampered'})

    def test_dispatcher_sees_every_log(self):
        logs = self.env['wm.collection.order.status.log'].with_user(self.dispatcher)
        self.assertEqual(
            logs.search([('id', 'in', (self.log_a | self.log_b).ids)]), self.log_a | self.log_b)

    def test_driver_cannot_edit_containers(self):
        container_type = self.env['wm.container.type'].create({'name': 'Rule Bin', 'code': 'RULEBIN'})
        container = self.env['wm.container'].create({
            'name': 'RULE-BIN-1', 'container_type_id': container_type.id,
            'collection_point_id': self.point.id})
        with self.assertRaises(AccessError):
            container.with_user(self.driver_a).write({'name': 'RULE-BIN-2'})

    def test_plain_internal_user_has_no_operational_access(self):
        for model in ('wm.collection.order', 'wm.collection.order.status.log', 'wm.billable.event'):
            if model in self.env:
                with self.assertRaises(AccessError, msg=model):
                    self.env[model].with_user(self.plain_user).search([])
