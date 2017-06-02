# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Cybrosys Technologies(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime
from dateutil import relativedelta
from odoo import models, fields, api
from odoo.tools.translate import _


class CrmTeam(models.Model):
    _name = "crm.target"

    def get_currency(self):
        return self.env.user.company_id.currency_id.id

    name = fields.Char(string='Name', required=True)
    user_id = fields.Many2one('res.users', 'Sales Person', required=True)
    sales_team = fields.Many2one('crm.team', string='Sales Team')
    target_amount = fields.Float('Target')
    date_from = fields.Date("Starting date", required=True)
    date_to = fields.Date("Ending date", required=True)
    duration = fields.Integer(default=1)
    currency_id = fields.Many2one('res.currency', store=True, string='Currency', readonly=True, default=lambda self: self.get_currency())

    @api.onchange('user_id')
    def onchange_salesman(self):
        team_ids = self.env['crm.team'].search([])
        dates = fields.Date

        for team_id in team_ids:
            for member_id in team_id.member_ids:
                if self.user_id == member_id:
                    self.sales_team = team_id.id

    @api.onchange('date_from', 'date_to')
    def get_duration(self):
        if self.date_from and self.date_to:
            r = relativedelta.relativedelta(datetime.strptime(self.date_to, "%Y-%m-%d"), datetime.strptime(self.date_from, "%Y-%m-%d"))

            t_day = datetime.strptime(self.date_to, "%Y-%m-%d").day
            t_month = datetime.strptime(self.date_to, "%Y-%m-%d").month
            t_year = datetime.strptime(self.date_to, "%Y-%m-%d").year

            f_day = datetime.strptime(self.date_from, "%Y-%m-%d").day
            f_month = datetime.strptime(self.date_from, "%Y-%m-%d").month
            f_year = datetime.strptime(self.date_from, "%Y-%m-%d").year
            if t_year < f_year:
                self.date_from = None
                self.date_to = None
                return {
                    'warning': {
                        'title': _('Warning!'),
                        'message': _('Please check the date'),
                    }
                }
            elif t_year == f_year and t_month < f_month:
                self.date_to = None
                self.date_from = None
                return {
                    'warning': {
                        'title': _('Warning!'),
                        'message': _('Please check the date'),
                    }
                }
            elif t_year == f_year and t_month == f_month and t_day < f_day:
                self.date_to = None
                self.date_from = None
                return {
                    'warning': {
                        'title': _('Warning!'),
                        'message': _('Please check the date'),
                    }
                }
            self.duration = r.months if r.months > 0 else 1

    def action_your_target(self):
        tree_res = self.env['ir.model.data'].get_object_reference('sales_team_parent', 'sales_target_tree_view')
        x = self.env['ir.model.data'].get_object_reference('sales_team_parent', 'action_crm_sales_target_act')

        tree_id = tree_res and tree_res[1] or False
        form_res = self.env['ir.model.data'].get_object_reference('sales_team_parent', 'sales_target_form_view')
        form_id = form_res and form_res[1] or False

        user_obj = self.env['res.users']

        u_id = user_obj.browse([self._uid])
        obj_target = self.env['crm.target'].search([])

        if u_id.has_group('sales_team.group_sale_salesman_all_leads') and u_id.has_group(
                    'sales_team.group_sale_salesman') and u_id.has_group('sales_team.group_sale_manager'):
            obj_target_list = obj_target.ids

        else:
            obj_target_list = []
            if obj_target:
                for obj in obj_target.ids:
                    print obj
                    if self.env['crm.target'].browse([obj]).user_id.id == self._uid:
                        obj_target_list.append(obj)

        return {
            'model': 'ir.actions.act_window',
            'name': 'Target',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'crm.target',
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'domain': [('id', 'in', obj_target_list)],
            'id': x[1],
        }


