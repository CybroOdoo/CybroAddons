# -*- coding: utf-8 -*-
###################################################################################
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Jesni Banu (<https://www.cybrosys.com>)
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
###################################################################################
from datetime import datetime
from odoo import models, fields, api, _


class HrLawsuit(models.Model):
    _name = 'hr.lawsuit'
    _description = 'Hr Lawsuit Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('hr.lawsuit')
        return super(HrLawsuit, self).create(vals)

    @api.multi
    def won(self):
        self.state = 'won'

    @api.multi
    def cancel(self):
        self.state = 'cancel'

    @api.multi
    def loss(self):
        self.state = 'fail'

    @api.multi
    def process(self):
        self.state = 'running'

    @api.depends('party2', 'employee_id')
    def set_party2(self):
        for each in self:
            if each.party2 == 'employee':
                each.party2_name = each.employee_id.name

    name = fields.Char(string='Code', copy=False)
    company_id = fields.Many2one('res.company', 'Company', readonly=True,
                                 default=lambda self: self.env.user.company_id)
    requested_date = fields.Date(string='Date', copy=False, readonly=1, default=datetime.now(),
                                 states={'draft': [('readonly', False)]})
    court_name = fields.Char(string='Court Name', track_visibility='always',
                             states={'won': [('readonly', True)]})
    judge = fields.Char(string='Judge', track_visibility='always', states={'won': [('readonly', True)]})
    lawyer = fields.Char(string='Lawyer', track_visibility='always', states={'won': [('readonly', True)]})
    party1 = fields.Many2one('res.company', string='Party 1', required=1, readonly=1,
                             states={'draft': [('readonly', False)]})
    party2 = fields.Selection([('employee', 'Employee')], default='employee',
                              string='Party 2', required=1, readonly=1, states={'draft': [('readonly', False)]})
    employee_id = fields.Many2one('hr.employee', string='Employee', copy=False,
                                  readonly=1, states={'draft': [('readonly', False)]})
    party2_name = fields.Char(compute='set_party2', string='Name', store=True)
    case_details = fields.Html(string='Case Details', copy=False, track_visibility='always')
    state = fields.Selection([('draft', 'Draft'),
                              ('running', 'Running'),
                              ('cancel', 'Cancelled'),
                              ('fail', 'Failed'),
                              ('won', 'Won')], string='Status',
                             default='draft', track_visibility='always', copy=False)


class HrLegalEmployeeMaster(models.Model):
    _inherit = 'hr.employee'

    legal_count = fields.Integer(compute='_legal_count', string='# Legal Actions')

    @api.multi
    def _legal_count(self):
        for each in self:
            legal_ids = self.env['hr.lawsuit'].search([('employee_id', '=', each.id)])
            each.legal_count = len(legal_ids)

    @api.multi
    def legal_view(self):
        for each1 in self:
            legal_obj = self.env['hr.lawsuit'].sudo().search([('employee_id', '=', each1.id)])
            legal_ids = []
            for each in legal_obj:
                legal_ids.append(each.id)
            view_id = self.env.ref('oh_hr_lawsuit_management.hr_lawsuit_form_view').id
            if legal_ids:
                if len(legal_ids) <= 1:
                    value = {
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'hr.lawsuit',
                        'view_id': view_id,
                        'type': 'ir.actions.act_window',
                        'name': _('Legal Actions'),
                        'res_id': legal_ids and legal_ids[0]
                    }
                else:
                    value = {
                        'domain': str([('id', 'in', legal_ids)]),
                        'view_type': 'form',
                        'view_mode': 'tree,form',
                        'res_model': 'hr.lawsuit',
                        'view_id': False,
                        'type': 'ir.actions.act_window',
                        'name': _('Legal Actions'),
                        'res_id': legal_ids
                    }

                return value


