# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aleena K (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.http import request


class SalesPerformance(models.TransientModel):
    """Wizard model for generating sales performance reports."""
    _name = 'sales.performance'
    _description = "Sales Performance Reports"

    start_date = fields.Date(
        string="Start Date",
        help="The start date"
    )
    end_date = fields.Date(
        string="End Date",
        help='The end date'
    )
    up_to_date_report = fields.Boolean(
        string="Report Up To Date",
        help='to get up to date report'
    )
    company_ids = fields.Many2many(
        comodel_name='res.company',
        string="Company",
        help='Res Company',
    )
    sales_team_ids = fields.Many2many(
        comodel_name='crm.team',
        string="Sales Team",
        domain="['|', "
               "('company_id', '=', False), "
               "('company_id', 'in', "
               "company_ids)]",
        help='Sales Team'
    )
    sales_person_ids = fields.Many2many(
        comodel_name='res.users',
        string="Sales Person",
        domain="[('sale_team_id', 'in', "
               "sales_team_ids)]",
        help='Sales Person',
    )
    warehouse_ids = fields.Many2many(
        comodel_name='stock.warehouse',
        string='Warehouse',
        help='stock warehouse',
        domain="[('company_id', 'in', "
               "company_ids)]"
    )

    @api.constrains('start_date', 'end_date')
    def _check_date_validation(self):
        """Ensure the end date is not earlier than the start date."""
        for record in self:
            if record.start_date and record.end_date:
                if record.end_date < record.start_date:
                    raise UserError(
                        "End Date must be greater than or equal to Start Date.")

    def sales_performance(self):
        """
           return: to sale order list view and form view
        """
        sales_person = []
        if self.sales_person_ids:
            for s_person in self.sales_person_ids:
                if s_person:
                    sales_person.append(s_person.id)
                    s_person.performance_values(s_person, self.start_date,
                                                self.end_date,
                                                self.up_to_date_report)
        elif self.sales_team_ids:
            for s_team in self.sales_team_ids:
                s_person = self.env['res.users'].search([
                    ('sale_team_id', '=', s_team.id)])
                for person in s_person:
                    sales_person.append(person.id)
                    person.performance_values(person, self.start_date,
                                              self.end_date,
                                              self.up_to_date_report)
        else:
            s_person = self.env['res.users'].search([
                ('company_id', 'in', self.company_ids.ids)])
            for rec in s_person:
                sales_person.append(rec.id)
                rec.performance_values(rec, self.start_date, self.end_date,
                                       self.up_to_date_report)
        list_view_id = request.env.ref(
            'sales_product_performance_report.view_res_users_report_list').id
        domain = [('id', 'in', sales_person) if sales_person else None]
        if sales_person:
            return {
                'name': 'Sales Performance Report',
                'res_model': 'res.users',
                'views': [(list_view_id, 'list')],
                'view_id': list_view_id,
                'type': 'ir.actions.act_window',
                'target': 'self',
                'domain': domain if sales_person else None,
                'context': {
                    'create': False,
                    'start_date': self.start_date if self.start_date else None,
                    'end_date': self.end_date if self.end_date else None,
                    'up_to_date': self.up_to_date_report,
                    'search_default_sale_team_id': [self.sales_team_ids.ids]
                    if self.sales_team_ids else None,
                },
            }
        else:
            raise UserError(f"No Sales Team in {self.company_ids.name}!" if
                            self.company_ids else (f"No Sales Team in "
                                                    f"Company!"))
