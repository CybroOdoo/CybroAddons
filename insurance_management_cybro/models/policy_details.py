# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields


class PolicyDetails(models.Model):
    _name = 'policy.details'

    name = fields.Char(string='Name', required=True)
    policy_type = fields.Many2one('policy.type', string='Policy Type', required=True)
    payment_type = fields.Selection([('fixed', 'Fixed'), ('installment', 'Installment')],
                                    required=True, default='fixed')
    amount = fields.Float(string='Amount', required=True)
    policy_duration = fields.Integer(string='Duration in Days', required=True)
    note_field = fields.Html(string='Comment')


class PolicyType(models.Model):
    _name = 'policy.type'

    name = fields.Char(string='Name')
