# -*- coding: utf-8 -*-
###################################################################################
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Treesa Maria Jude  (<https://www.cybrosys.com>)
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
from odoo import models, fields


class HrPopupReminder(models.Model):
    _name = 'hr.reminder'

    name = fields.Char(string='Title', required=True)
    model_name = fields.Many2one('ir.model', string="Model", required=True,  domain="[('model', 'like','hr')]")
    model_field = fields.Many2one('ir.model.fields', string='Field',
                                  domain="[('model_id', '=',model_name),('ttype', 'in', ['datetime','date'])]",
                                  required=True)
    search_by = fields.Selection([('today', 'Today'),
                                  ('set_period', 'Set Period'),
                                  ('set_date', 'Set Date'), ],
                                 required=True, string="Search By")
    days_before = fields.Integer(string='Reminder before')
    active = fields.Boolean(string="Active",default=True)
    # exclude_year = fields.Boolean(string="Consider day alone")
    reminder_active = fields.Boolean(string="Reminder Active")
    date_set = fields.Date(string='Select Date')
    date_from = fields.Date(string="Start Date")
    date_to = fields.Date(string="End Date")
    expiry_date = fields.Date(string="Reminder Expiry Date")
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)

    def reminder_scheduler(self):
        now = fields.Datetime.from_string(fields.Datetime.now())
        today = fields.Date.today()
        obj = self.env['hr.reminder'].search([])
        for i in obj:
            if i.search_by != "today":
                if i.expiry_date and datetime.strptime(today, "%Y-%m-%d") == datetime.strptime(i.expiry_date, "%Y-%m-%d"):
                    i.active = False
                else:
                        if i.search_by == "set_date":
                            d1 = datetime.strptime(i.date_set, "%Y-%m-%d")
                            d2 = datetime.strptime(today, "%Y-%m-%d")
                            daydiff = abs((d2 - d1).days)
                            if daydiff <= i.days_before:
                                i.reminder_active = True
                            else:
                                i.reminder_active = False
                        elif i.search_by == "set_period":
                            d1 = datetime.strptime(i.date_from, "%Y-%m-%d")
                            d2 = datetime.strptime(today, "%Y-%m-%d")
                            daydiff = abs((d2 - d1).days)
                            if daydiff <= i.days_before:
                                i.reminder_active = True
                            else:
                                i.reminder_active = False
            else:
                i.reminder_active = True

