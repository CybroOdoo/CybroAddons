# -*- coding: utf-8 -*-
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
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSalesTeamAccess(TransactionCase):
    """Record visibility for Team Members, Team Leaders and the standard
    salesperson / manager groups that the module must leave untouched."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context,
                                       no_reset_password=True,
                                       tracking_disable=True))
        member_group = ('sales_team_access_controls.'
                        'sales_team_access_controls_group_team_member')
        leader_group = ('sales_team_access_controls.'
                        'sales_team_access_controls_group_team_leader')
        cls.member_1 = cls._create_user('stac_member_1', member_group)
        cls.member_2 = cls._create_user('stac_member_2', member_group)
        cls.leader = cls._create_user('stac_leader', leader_group)
        cls.other_member = cls._create_user('stac_other_member', member_group)
        cls.other_leader = cls._create_user('stac_other_leader', leader_group)
        cls.own_docs = cls._create_user(
            'stac_own_docs', 'sales_team.group_sale_salesman')
        cls.all_docs = cls._create_user(
            'stac_all_docs', 'sales_team.group_sale_salesman_all_leads')
        cls.manager = cls._create_user(
            'stac_manager', 'sales_team.group_sale_manager')

        Team = cls.env['crm.team']
        cls.team = Team.create({
            'name': 'STAC Team A',
            'user_id': cls.leader.id,
            'member_ids': [(6, 0, [cls.member_1.id, cls.member_2.id])],
        })
        cls.other_team = Team.create({
            'name': 'STAC Team B',
            'user_id': cls.other_leader.id,
            'member_ids': [(6, 0, [cls.other_member.id])],
        })

        Partner = cls.env['res.partner']
        cls.customer_1 = Partner.create({
            'name': 'STAC Customer 1', 'user_id': cls.member_1.id})
        cls.customer_2 = Partner.create({
            'name': 'STAC Customer 2', 'user_id': cls.member_2.id})
        cls.customer_other = Partner.create({
            'name': 'STAC Customer B', 'user_id': cls.other_member.id})
        cls.product = cls.env['product.product'].create({
            'name': 'STAC Product', 'list_price': 10.0})

        cls.order_member_1 = cls._create_order(
            cls.member_1, cls.team, cls.customer_1)
        cls.order_member_2 = cls._create_order(
            cls.member_2, cls.team, cls.customer_2)
        cls.order_leader = cls._create_order(
            cls.leader, cls.team, cls.customer_1)
        cls.order_other = cls._create_order(
            cls.other_member, cls.other_team, cls.customer_other)
        cls.order_unassigned = cls._create_order(
            False, False, cls.customer_other)
        cls.orders = (cls.order_member_1 | cls.order_member_2
                      | cls.order_leader | cls.order_other
                      | cls.order_unassigned)

        Lead = cls.env['crm.lead']
        cls.lead_member_1 = Lead.create({
            'name': 'STAC Lead 1', 'user_id': cls.member_1.id,
            'team_id': cls.team.id})
        cls.lead_member_2 = Lead.create({
            'name': 'STAC Lead 2', 'user_id': cls.member_2.id,
            'team_id': cls.team.id})
        cls.lead_other = Lead.create({
            'name': 'STAC Lead B', 'user_id': cls.other_member.id,
            'team_id': cls.other_team.id})
        cls.lead_unassigned = Lead.create({
            'name': 'STAC Lead Free', 'user_id': False, 'team_id': False})
        cls.leads = (cls.lead_member_1 | cls.lead_member_2
                     | cls.lead_other | cls.lead_unassigned)

    @classmethod
    def _create_user(cls, login, group_xmlid):
        return cls.env['res.users'].create({
            'name': login,
            'login': login,
            'email': f'{login}@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id,
                                  cls.env.ref(group_xmlid).id])],
        })

    @classmethod
    def _create_order(cls, user, team, partner):
        return cls.env['sale.order'].create({
            'partner_id': partner.id,
            'user_id': user.id if user else False,
            'team_id': team.id if team else False,
            'order_line': [(0, 0, {'product_id': cls.product.id,
                                   'product_uom_qty': 1.0})],
        })

    def _visible_orders(self, user):
        return self.env['sale.order'].with_user(user).search(
            [('id', 'in', self.orders.ids)])

    def _visible_leads(self, user):
        return self.env['crm.lead'].with_user(user).search(
            [('id', 'in', self.leads.ids)])

    # ------------------------------------------------------------------
    # Groups
    # ------------------------------------------------------------------
    def test_groups_imply_salesperson(self):
        """Team roles give sales rights; the leader is also a member."""
        self.assertTrue(self.member_1.has_group(
            'sales_team.group_sale_salesman'))
        self.assertTrue(self.leader.has_group(
            'sales_team_access_controls.'
            'sales_team_access_controls_group_team_member'))

    # ------------------------------------------------------------------
    # Team Member
    # ------------------------------------------------------------------
    def test_member_sees_only_own_orders_and_leads(self):
        self.assertEqual(self._visible_orders(self.member_1),
                         self.order_member_1)
        self.assertEqual(self._visible_leads(self.member_1),
                         self.lead_member_1)

    def test_member_sees_only_own_order_lines(self):
        lines = self.env['sale.order.line'].with_user(self.member_1).search(
            [('order_id', 'in', self.orders.ids)])
        self.assertEqual(lines, self.order_member_1.order_line)

    def test_member_cannot_read_or_write_colleague_records(self):
        with self.assertRaises(AccessError):
            self.order_member_2.with_user(self.member_1).read(['name'])
        with self.assertRaises(AccessError):
            self.order_member_2.with_user(self.member_1).write(
                {'note': 'x'})
        with self.assertRaises(AccessError):
            self.lead_member_2.with_user(self.member_1).read(['name'])
        with self.assertRaises(AccessError):
            self.order_unassigned.with_user(self.member_1).read(['name'])

    def test_member_cannot_delete_own_order(self):
        """Members get create/read/write only, never delete."""
        with self.assertRaises(AccessError):
            self.order_member_1.with_user(self.member_1).unlink()

    def test_member_creates_own_order_lead_and_contact(self):
        env = self.env(user=self.member_1)
        contact = env['res.partner'].create({'name': 'STAC New Contact'})
        order = env['sale.order'].create({
            'partner_id': contact.id,
            'order_line': [(0, 0, {'product_id': self.product.id})],
        })
        self.assertEqual(order.user_id, self.member_1)
        lead = env['crm.lead'].create({'name': 'STAC Own Lead'})
        self.assertEqual(lead.user_id, self.member_1)
        self.assertEqual(contact.with_user(self.member_1).name,
                         'STAC New Contact')

    def test_member_contacts(self):
        Partner = self.env['res.partner'].with_user(self.member_1)
        visible = Partner.search([('id', 'in', (
            self.customer_1 | self.customer_2 | self.customer_other).ids)])
        self.assertEqual(visible, self.customer_1)
        # Internal users and the own company stay readable.
        self.assertTrue(Partner.browse(self.member_2.partner_id.id).name)
        self.assertTrue(Partner.browse(self.env.company.partner_id.id).name)

    def test_member_reads_partner_used_on_own_order(self):
        """A contact of another salesperson stays readable when it is the
        customer of an order the member can read."""
        order = self._create_order(self.member_1, self.team,
                                   self.customer_other)
        self.assertEqual(
            order.with_user(self.member_1).partner_id.name,
            'STAC Customer B')

    # ------------------------------------------------------------------
    # Team Leader
    # ------------------------------------------------------------------
    def test_leader_sees_own_and_team_records(self):
        self.assertEqual(
            self._visible_orders(self.leader),
            self.order_member_1 | self.order_member_2 | self.order_leader)
        self.assertEqual(self._visible_leads(self.leader),
                         self.lead_member_1 | self.lead_member_2)

    def test_leader_does_not_see_other_team(self):
        with self.assertRaises(AccessError):
            self.order_other.with_user(self.leader).read(['name'])
        with self.assertRaises(AccessError):
            self.lead_other.with_user(self.leader).read(['name'])
        self.assertEqual(self._visible_orders(self.other_leader),
                         self.order_other)

    def test_leader_edits_team_member_order(self):
        self.order_member_2.with_user(self.leader).write(
            {'note': 'Checked by leader'})
        self.assertIn('Checked by leader', str(self.order_member_2.note))

    def test_leader_opens_and_edits_team_order_lines(self):
        """The leader can open a team member's order with its lines."""
        lines = self.order_member_2.with_user(self.leader).order_line
        self.assertEqual(lines.read(['product_uom_qty'])[0]['product_uom_qty'], 1.0)
        lines.write({'product_uom_qty': 3.0})
        self.assertEqual(self.order_member_2.order_line.product_uom_qty, 3.0)
        with self.assertRaises(AccessError):
            self.order_other.order_line.with_user(self.leader).read(['product_uom_qty'])

    def test_leader_contacts(self):
        visible = self.env['res.partner'].with_user(self.leader).search(
            [('id', 'in', (self.customer_1 | self.customer_2
                           | self.customer_other).ids)])
        self.assertEqual(visible, self.customer_1 | self.customer_2)

    # ------------------------------------------------------------------
    # Standard Odoo groups are not affected
    # ------------------------------------------------------------------
    def test_all_documents_salesperson_unaffected(self):
        self.assertEqual(self._visible_orders(self.all_docs), self.orders)
        self.assertEqual(self._visible_leads(self.all_docs), self.leads)

    def test_own_documents_salesperson_unaffected(self):
        """Odoo's standard rule: own records plus unassigned ones."""
        self.assertEqual(self._visible_orders(self.own_docs),
                         self.order_unassigned)
        self.assertEqual(self._visible_leads(self.own_docs),
                         self.lead_unassigned)

    def test_sales_manager_unaffected(self):
        self.assertEqual(self._visible_orders(self.manager), self.orders)
        self.assertEqual(self._visible_leads(self.manager), self.leads)
        self.assertEqual(
            self.env['res.partner'].with_user(self.manager).search_count(
                [('id', '=', self.customer_other.id)]), 1)

    def test_manager_with_member_role_keeps_full_access(self):
        self.manager.group_ids = [(4, self.env.ref(
            'sales_team_access_controls.'
            'sales_team_access_controls_group_team_member').id)]
        self.assertEqual(self._visible_orders(self.manager), self.orders)

    def test_core_rules_untouched(self):
        """The module must not alter the standard sale / CRM rules."""
        for xmlid in ('sale.sale_order_see_all', 'crm.crm_rule_all_lead_1'):
            self.assertTrue(self.env.ref(xmlid).active, xmlid)
        for xmlid in ('sale.sale_order_personal_rule',
                      'crm.crm_rule_personal_lead'):
            self.assertIn("('user_id','=',False)",
                          self.env.ref(xmlid).domain.replace(' ', ''),
                          xmlid)
