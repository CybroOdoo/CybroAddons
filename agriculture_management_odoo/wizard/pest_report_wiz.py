# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import fields, models


class CropReport(models.TransientModel):
    _name = 'pest.report.wizard'
    _description = 'Pest Report Wizard'

    date_from = fields.Date(string='From Date')
    date_to = fields.Date(string='To Date')

    def action_pdf_report(self):
        ret = """select pest_request.reference, res_partner.name, crop_requests.ref,
                pest_request.disease, pest_details.pest_name,pest_request.pest_quantity,
                pest_request.pest_cost, pest_request.total_cost,pest_request.state from pest_request
                inner join res_partner on pest_request.farmer_id = res_partner.id
                inner join crop_requests on crop_requests.id = pest_request.crop_id
                inner join pest_details on pest_details.id = pest_request.pest_id"""
        if self.date_from and self.date_to:
            ret = ret + """ where crop_requests.request_date > '""" + str(
                self.date_from) + """' AND crop_requests.request_date < '""" + str(
                self.date_to) + """'"""
        self.env.cr.execute(ret)
        record = self.env.cr.fetchall()
        data = {
            'form': self.read()[0],
            'date_to': self.date_to,
            'date_from': self.date_from,
            'record': record
        }
        return self.env.ref(
            'agriculture_management_odoo.action_crop_request_report').report_action(
            self, data=data)
