# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vyshnav AR(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.exceptions import UserError
from odoo import fields, models, _


class PestReport(models.TransientModel):
    """ Model for creating pest request report """
    _name = 'pest.report'
    _description = 'Pest Report in Pest Request'

    date_from = fields.Date(string='From Date', help=' Start date of report')
    date_to = fields.Date(string='To Date', help=' End date of report')

    def action_pdf_report(self):
        """ Function for pest request pdf report """
        ret = """select pest_request.reference, res_partner.name, crop_request.ref,
            pest_request.disease, pest_detail.pest_name as pest_name,
            pest_detail.pest_cost as cost,pest_request.pest_quantity,
            pest_request.total_cost,pest_request.state from pest_request
            inner join res_partner on pest_request.farmer_id = res_partner.id
            inner join crop_request on crop_request.id = pest_request.crop_id
            inner join pest_detail on pest_detail.id = pest_request.pest_id"""
        today = fields.Date.today()
        if self.date_from and not self.date_to:
            if self.date_from > today:
                raise UserError(
                    _('You could not set the start date or the '
                      'end date in the future.'))
            else:
                ret = ret + """ where pest_request.request_date >= '""" + str(
                    self.date_from) + """' AND pest_request.request_date <= 
                    '""" \
                      + str(
                    today) + """'"""
        if self.date_to and not self.date_from:
            if self.date_to > today:
                raise UserError(
                    _('You could not set the start date or the end '
                      'date in the future.'))
            else:
                ret = ret + """ where pest_request.request_date <= '""" + str(
                    self.date_to) + """'"""
        if self.date_from and self.date_to:
            if self.date_from <= self.date_to:
                ret = ret + """ where pest_request.request_date >= '""" + \
                      str(self.date_from) + """' AND pest_request.request_date 
                      <= '""" \
                      + str(self.date_to) + """'"""
            else:
                raise UserError(
                    _('The start date must be inferior to the end date.'))
        self.env.cr.execute(ret)
        record = self.env.cr.fetchall()
        data = {
            'form': self.read()[0],
            'date_to': self.date_to,
            'date_from': self.date_from,
            'record': record
        }
        return self.env.ref(
            'agriculture_management_odoo.pest_request_report_action').report_action(
            self, data=data)
