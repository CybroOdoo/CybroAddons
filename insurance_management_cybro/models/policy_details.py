# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import fields, models


class PolicyDetails(models.Model):
    _name = 'policy.details'

    name = fields.Char(string='Name', required=True)
    policy_type_id = fields.Many2one(
        'policy.type', string='Policy Type', required=True)
    payment_type = fields.Selection(
        [('fixed', 'Fixed'), ('installment', 'Installment')],
        required=True, default='fixed')
    currency_id = fields.Many2one(
        'res.currency', string='Currency', required=True,
        default=lambda self: self.env.user.company_id.currency_id.id)
    amount = fields.Monetary(string='Amount', required=True)
    policy_duration = fields.Integer(string='Duration in Days', required=True)
    note_field = fields.Html(string='Comment')


class PolicyType(models.Model):
    _name = 'policy.type'

    name = fields.Char(string='Name')
