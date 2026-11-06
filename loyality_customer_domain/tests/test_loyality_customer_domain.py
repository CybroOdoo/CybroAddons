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
#############################################################################
from odoo.exceptions import ValidationError
from odoo.fields import Command
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestLoyaltyCustomerDomain(TransactionCase):
    """Test the customer domain of the loyalty rules on sale orders."""

    @classmethod
    def setUpClass(cls):
        """Create two customers, a product and a promotion for the
        customers of a tag."""
        super().setUpClass()
        cls.env['loyalty.program'].search([]).active = False
        cls.vip_tag = cls.env['res.partner.category'].create({'name': 'VIP'})
        cls.vip = cls.env['res.partner'].create({
            'name': 'VIP Customer', 'category_id': [Command.set(cls.vip_tag.ids)]})
        cls.regular = cls.env['res.partner'].create({'name': 'Regular Customer'})
        cls.product = cls.env['product.product'].create({
            'name': 'Desk', 'list_price': 100.0, 'taxes_id': False})
        cls.vip_promotion = cls._program(
            'VIP Promotion', f"[('category_id', 'in', [{cls.vip_tag.id}])]")

    @classmethod
    def _program(cls, name, customer_domain='[]', **rule_values):
        return cls.env['loyalty.program'].create({
            'name': name,
            'program_type': 'promotion',
            'trigger': 'auto',
            'applies_on': 'current',
            'rule_ids': [Command.create({
                'reward_point_mode': 'order',
                'reward_point_amount': 1,
                'minimum_qty': 1,
                'customer_domain': customer_domain,
                **rule_values,
            })],
            'reward_ids': [Command.create({
                'reward_type': 'discount',
                'discount': 10,
                'discount_mode': 'percent',
                'discount_applicability': 'order',
                'required_points': 1,
            })],
        })

    def _order(self, partner, qty=1):
        return self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [Command.create({
                'product_id': self.product.id, 'product_uom_qty': qty})],
        })

    def _status(self, order, program):
        return order._program_check_compute_points(program)[program]

    def test_01_matching_customer(self):
        """A customer of the domain gets the points of the rule."""
        status = self._status(self._order(self.vip), self.vip_promotion)
        self.assertNotIn('error', status)
        self.assertEqual(status['points'], [1])

    def test_02_other_customer(self):
        """Another customer cannot use the program."""
        status = self._status(self._order(self.regular), self.vip_promotion)
        self.assertEqual(status.get('error'),
                         "This program is not available for this customer.")

    def test_03_program_without_customer_domain(self):
        """A program without customer domain still applies to everyone."""
        everyone = self._program('Everyone')
        for partner in (self.vip, self.regular):
            status = self._status(self._order(partner), everyone)
            self.assertEqual(status.get('points'), [1], partner.name)

    def test_04_programs_are_independent(self):
        """A customer matching one program does not unlock another."""
        other_tag = self.env['res.partner.category'].create({'name': 'Gold'})
        gold_promotion = self._program(
            'Gold Promotion', f"[('category_id', 'in', [{other_tag.id}])]")
        order = self._order(self.vip)
        result = order._program_check_compute_points(
            self.vip_promotion | gold_promotion)
        self.assertEqual(result[self.vip_promotion]['points'], [1])
        self.assertIn('error', result[gold_promotion])

    def test_05_other_conditions_still_apply(self):
        """A customer of the domain still needs the minimum quantity."""
        promotion = self._program(
            'VIP Bulk', f"[('id', '=', {self.vip.id})]", minimum_qty=5)
        status = self._status(self._order(self.vip, qty=2), promotion)
        self.assertIn('error', status)
        self.assertNotEqual(
            status['error'], "This program is not available for this customer.")
        self.assertEqual(self._status(self._order(self.vip, qty=5),
                                      promotion)['points'], [1])

    def test_06_reward_applied_on_order(self):
        """The automatic promotion discounts the order of a customer of the
        domain only."""
        vip_order, regular_order = self._order(self.vip), self._order(self.regular)
        for order in (vip_order, regular_order):
            order._update_programs_and_rewards()
            # Claim the reward like the reward button of the order does
            coupon = order.coupon_point_ids.coupon_id.filtered(
                lambda card: card.program_id == self.vip_promotion)
            if coupon:
                order._apply_program_reward(
                    self.vip_promotion.reward_ids, coupon)
        self.assertTrue(vip_order.order_line.filtered('is_reward_line'))
        self.assertFalse(regular_order.order_line.filtered('is_reward_line'))
        self.assertEqual(vip_order.amount_untaxed, 90.0)
        self.assertEqual(regular_order.amount_untaxed, 100.0)

    def test_07_invalid_customer_domain(self):
        """A malformed or dynamic customer domain is refused when saved, so
        that it never breaks the orders."""
        rule = self.vip_promotion.rule_ids
        for domain in ("[('category_id', 'in'", "[('user_id', '=', uid)]",
                       "[('no_such_field', '=', 1)]"):
            with self.subTest(domain=domain), \
                    self.assertRaises(ValidationError):
                rule.customer_domain = domain

    def test_08_salesperson(self):
        """A salesperson who only sees their own documents gets the
        promotion on the orders of the customers of the domain."""
        user = new_test_user(
            self.env, login='loyalty_salesman',
            groups='base.group_user,sales_team.group_sale_salesman')
        env = self.env(user=user)
        orders = env['sale.order'].create([{
            'partner_id': partner.id,
            'order_line': [Command.create({
                'product_id': self.product.id, 'product_uom_qty': 1})],
        } for partner in (self.vip, self.regular)])
        program = env['loyalty.program'].browse(self.vip_promotion.id)
        vip_status, regular_status = (
            order._program_check_compute_points(program)[program]
            for order in orders)
        self.assertEqual(vip_status['points'], [1])
        self.assertEqual(regular_status.get('error'),
                         "This program is not available for this customer.")
