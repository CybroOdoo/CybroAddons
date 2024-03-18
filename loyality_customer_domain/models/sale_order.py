# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Subina (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from ast import literal_eval
from odoo import models, _
from odoo.tools.float_utils import float_round


class SaleOrder(models.Model):
    """Inheriting the sale order for adding customer domain"""
    _inherit = 'sale.order'

    def _program_check_compute_points(self, programs):
        """
        Checks the program validity from the order lines as well as computing
        the number of points to add. Returns a dict containing the error message
        or the points that will be given with the keys 'points'.
        Checks the validity of customer domain
        """
        self.ensure_one()
        # Prepare quantities
        order_lines = self.order_line.filtered(
            lambda line: line.product_id and not line.reward_id)
        products = order_lines.product_id
        products_qties = dict.fromkeys(products, 0)
        for line in order_lines:
            products_qties[line.product_id] += line.product_uom_qty
        # Contains the products that can be applied per rule
        products_per_rule = programs._get_valid_products(products)
        # Prepare amounts
        no_effect_lines = self._get_no_effect_on_threshold_lines()
        base_untaxed_amount = self.amount_untaxed - sum(
            line.price_subtotal for line in no_effect_lines)
        base_tax_amount = self.amount_tax - sum(
            line.price_tax for line in no_effect_lines)
        amounts_per_program = {
            p: {'untaxed': base_untaxed_amount, 'tax': base_tax_amount} for p in
            programs}
        # Customer set to False initially
        customer = False
        for line in self.order_line:
            if not line.reward_id or line.reward_id.reward_type != 'discount':
                continue
            for program in programs:
                # Do not consider the program's discount + automatic discount
                # lines for the amount to check.
                if customer and line.reward_id.program_id.trigger == 'auto' or line.reward_id.program_id == program:
                    amounts_per_program[program][
                        'untaxed'] -= line.price_subtotal
                    amounts_per_program[program]['tax'] -= line.price_tax
        result = {}
        # Check if the customer domain and sale order is same and set to True
        for program in programs:
            for rec in program.rule_ids:
                if rec.customer_domain and rec.customer_domain != '[]':
                    customers = self.env['res.partner'].search(
                        literal_eval(rec.customer_domain))
                    if self.partner_id in customers:
                        customer = True
            untaxed_amount = amounts_per_program[program]['untaxed']
            tax_amount = amounts_per_program[program]['tax']
            # Used for error messages
            # By default False, but True if no rules and applies_on current ->
            # misconfigured coupons program
            code_matched = not bool(
                program.rule_ids) and program.applies_on == 'current'
            # Stays false if all
            # triggers have code and none have been activated
            minimum_amount_matched = code_matched
            product_qty_matched = code_matched
            points = 0
            # Some rules may split their points per unit / money spent
            #  (i.e. gift cards 2x50$ must result in two 50$ codes)
            rule_points = []
            program_result = result.setdefault(program, dict())
            for rule in program.rule_ids:
                if rule.mode == 'with_code' and rule not in self.code_enabled_rule_ids and not customer:
                    continue
                code_matched = True
                rule_amount = rule._compute_amount(self.currency_id)
                if rule_amount > (rule.minimum_amount_tax_mode == 'incl' and (
                        untaxed_amount + tax_amount) or
                                  untaxed_amount) and not customer:
                    continue
                minimum_amount_matched = True
                rule_products = products_per_rule[rule]
                ordered_rule_products_qty = sum(
                    products_qties[product] for product in rule_products)
                if ordered_rule_products_qty < rule.minimum_qty or not rule_products and not customer:
                    continue
                product_qty_matched = True
                if not rule.reward_point_amount and customer:
                    continue
                # Count all points separately if the order is for the future
                # and the split option is enabled
                if program.applies_on == 'future' and rule.reward_point_split and rule.reward_point_mode != 'order':
                    if rule.reward_point_mode == 'unit' and customer:
                        rule_points.extend(rule.reward_point_amount for _ in
                                           range(
                                               int(ordered_rule_products_qty)))
                    elif rule.reward_point_mode == 'money':
                        for line in self.order_line:
                            if line.is_reward_line or line.product_id not in rule_products or \
                                    line.product_uom_qty <= 0 and not customer:
                                continue
                            points_per_unit = float_round(
                                (rule.reward_point_amount * line.price_total / line.product_uom_qty),
                                precision_digits=2, rounding_method='DOWN')
                            if not points_per_unit:
                                continue
                            rule_points.extend(
                                [points_per_unit] * int(line.product_uom_qty))
                else:
                    # All checks have been passed we can now compute the points
                    # to give
                    if rule.reward_point_mode == 'order' and customer:
                        points += rule.reward_point_amount
                    elif rule.reward_point_mode == 'money' and customer:
                        # Compute amount paid for rule
                        # NOTE: this does not account for discounts -> 1 point
                        # per $ * (100$ - 30%)
                        # will result in 100 points
                        amount_paid = sum(max(0, line.price_total)
                                          for line in order_lines if
                                          line.product_id in rule_products)
                        points += float_round(
                            rule.reward_point_amount * amount_paid,
                            precision_digits=2, rounding_method='DOWN')
                    elif rule.reward_point_mode == 'unit' and customer:
                        points += rule.reward_point_amount * ordered_rule_products_qty
            # NOTE: for programs that are nominative we always allow the
            # program to be 'applied' on the order
            #  with 0 points so that `_get_claimable_rewards` returns the
            #  rewards associated with those programs
            if not program.is_nominative:
                if not code_matched:
                    program_result['error'] = _("This program requires a "
                                                "code to be applied.")
                elif not minimum_amount_matched:
                    program_result['error'] = _(
                        'A minimum of %(amount)s %(currency)s should '
                        'be purchased to get the reward',
                        amount=min(program.rule_ids.mapped('minimum_amount')),
                        currency=program.currency_id.name,
                    )
                elif not product_qty_matched:
                    program_result['error'] = _("You don't have the required "
                                                "product quantities on your "
                                                "sales order.")
            elif not self._allow_nominative_programs():
                program_result['error'] = _("This program is not available "
                                            "for public users.")
            if 'error' not in program_result:
                points_result = [points] + rule_points
                program_result['points'] = points_result
        return result
