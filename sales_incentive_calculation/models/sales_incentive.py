# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: ASWIN A K (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1) It is forbidden to publish, distribute, sublicense, or sell
#    copies of the Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
#    THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SalesIncentive(models.Model):
    """
    This class represents the Sales Incentive model, which is used to configure
    incentive schemes for sales personnel. It allows defining various parameters
    such as the calculation method, incentive tiers, and activation status.
    """
    _name = 'sales.incentive'
    _description = 'Sales Incentive'

    name = fields.Char(
        string='Name',
        help='Enter the name for your record. This field is required.',
        required=True)
    calculation_method = fields.Selection(
        [('linear', 'Linear'), ('step', 'Tiered Commission Plan')],
        help='Tired : the amount of Incentive '
             'increases as the sales person achieves more.',
        string='Based On', default='linear')
    select_incentive_ids = fields.One2many(
        'select.incentive', 'sales_incentive_id')
    active_calculation = fields.Boolean(
        string='Active',
        copy=False,
        help='This field controls whether the scheme is active or not.')

    @api.onchange('active_calculation')
    def _onchange_active_calculation(self):
        """
            Checks for any active_calculation, if any returns a user error.
        """
        if self.search([('active_calculation', '=', True)]):
            if self.active_calculation:
                raise UserError(
                    _('Another scheme already active for incentive calculation')
                )

    def action_incentive_compute(self):
        """
            Computes calculate_incentive and returns it.
        """
        calc = self.env['calculate.incentive'].search([])
        challenge = self.env['gamification.challenge'].search(
            [('incentive_calculation', '=', True)])
        docs = self.env['gamification.goal'].search(
            [('challenge_id', 'in', challenge.ids)])
        self.send_warnings(challenge, docs)
        unlink_date_list = self.filter_expired_calc_records(calc, docs)
        self.unlink_expired_calc_records(unlink_date_list)
        for goal in docs:
            incentive = 0.0
            if self.calculation_method == 'linear':
                incentive = self.calculate_linear_incentive(goal, incentive)
            else:
                incentive = self.calculate_tiered_incentive(goal)
            data = {
                'salesperson_id': goal.user_id.id,
                'goal': goal.target_goal,
                'achieved': goal.current,
                'achievement_percentage': goal.target_achievement_percentage,
                'incentive': incentive,
                'start_date': goal.start_date,
                'end_date': goal.end_date,
                'status': 'unpaid',
            }
            self.env['calculate.incentive'].create(data)
        return {
            'name': 'Incentive',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'calculate.incentive',
            'target': 'current',
        }

    def calculate_linear_incentive(self, goal, incentive, highest=0):
        """Find the incentive by using linear method"""
        for select_line in self.select_incentive_ids:
            if ((goal.target_achievement_percentage >=
                 select_line.upto_percent)
                    and (select_line.upto_percent > highest)):
                highest = select_line.upto_percent
                if select_line.incentive_type == 'percent':
                    incentive = goal.current * (
                            select_line.reward / 100)
                else:
                    incentive = select_line.reward
        goal.incentive = incentive
        return incentive

    def send_warnings(self, challenge, docs):
        """It is a method to raise warnings
        :param1 challenge
        :param2 docs that is goals of the challenge
        """
        if not (challenge and docs):
            raise UserError(
                _('There is on active challenge and goal for calculation'))
        if docs.filtered(lambda goal: not goal.end_date):
            error_users = "'s,  ".join(docs.mapped('user_id.name'))
            raise UserError(
                _(f"The goal {error_users}'s "
                  f"{docs[0].display_name} has no end date."))

    def filter_expired_calc_records(self, calc, docs):
        """
        Filter calculate_incentive records based on expiration date.
        """
        unlink_date_list = []
        for record in calc:
            if record.end_date >= (fields.Date.today()):
                record.unlink()
            elif docs[0].end_date == record.end_date:
                unlink_date_list.append(record.id)
        return unlink_date_list

    def unlink_expired_calc_records(self, unlink_date_list):
        """
        Unlink expired calculate_incentive records.
        """
        self.env['calculate.incentive'].search(
            [('id', 'in', unlink_date_list)]).unlink()

    def calculate_tiered_incentive(self, goal):
        """
        Calculate incentive for tiered commission plan.
        """
        incentive = 0.0
        sum_value = 0.0
        old = 0.0
        final_incentive = 0.0

        for select_line in self.select_incentive_ids.sorted(
                lambda x: x.upto_percent):
            if (goal.target_achievement_percentage
                    >= select_line.upto_percent):
                new = (goal.target_goal * (
                        select_line.upto_percent / 100)) - old
                sum_value += new
                if select_line.incentive_type == 'percent':
                    incentive += new * (select_line.reward / 100)
                else:
                    incentive += select_line.reward
                old = goal.target_goal * (
                        select_line.upto_percent / 100)
            elif sum_value < goal.current and sum_value != 0.0:
                last_incentive = goal.current - sum_value
                if select_line.incentive_type == 'percent':
                    final_incentive = last_incentive * (
                            select_line.reward / 100)
                else:
                    final_incentive = select_line.reward
                sum_value += goal.current - sum_value
        incentive += final_incentive
        goal.incentive = incentive
        return incentive
