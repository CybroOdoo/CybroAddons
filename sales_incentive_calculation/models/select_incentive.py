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
from odoo import fields, models


class IncentiveSettings(models.Model):
    """This model is used to handle incentive criteria"""
    _name = 'select.incentive'
    _description = 'Select Incentive Settings'

    upto_percent = fields.Float(
        string='Achievement %',
        help='This field represents the percentage of the achievement.')
    reward = fields.Float(string='Reward', help='Specify the reward amount')
    incentive_type = fields.Selection(
        [('percent', 'Percentage'),
         ('amount', 'Amount')], string='Type', default='percent',
        help='Whether the reward is calculated as a percentage or an amount.')
    sales_incentive_id = fields.Many2one(
        'sales.incentive',
        'Incentive',
        help='This field establishes a link between the '
             'current record and a specific sales incentive.')
