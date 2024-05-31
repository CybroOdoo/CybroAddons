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


class CropReport(models.TransientModel):
    """ Model for creating report for crop request """
    _name = 'crop.report'
    _description = 'Crop Report In Crop Request'

    date_from = fields.Date(string='From Date', help=' Start date of report')
    date_to = fields.Date(string='To Date', help='End date of report')

    def action_pdf_report(self):
        """ Function for crop request pdf report """
        ret = """select crop_request.ref, res_partner.name, 
                    seed_detail.name, crop_request.request_date,
                    crop_request.state,
                    location_detail.location_name from crop_request
                    inner join farmer_detail ON 
                    crop_request.farmer_id = farmer_detail.id
                    inner join res_partner ON
                    farmer_detail.farmer_id = res_partner.id
                    inner join seed_detail ON 
                    crop_request.seed_id = seed_detail.id
                    inner join location_detail ON
                    crop_request.location_id = location_detail.id"""
        today = fields.Date.today()
        if self.date_from and not self.date_to:
            if self.date_from > today:
                raise UserError(
                    _('You could not set the start date or '
                      'the end date in the future.'))
            else:
                ret = ret + """ where crop_request.request_date >= '""" + str(
                    self.date_from) + """' AND crop_request.request_date <= '""" \
                      + str(
                    today) + """'"""
        if self.date_to and not self.date_from:
            if self.date_to > today:
                raise UserError(
                    _('You could not set the start date or the end '
                      'date in the future.'))
            else:
                ret = ret + """ where crop_request.request_date <= '""" + str(
                    self.date_to) + """'"""
        if self.date_from and self.date_to:
            if self.date_from <= self.date_to:
                ret = ret + """ where crop_request.request_date >= '""" + \
                      str(self.date_from) + """' AND crop_request.request_date <= '""" \
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
        return (self.env.ref(
            'agriculture_management_odoo.action_crop_request_report').report_action(
            self, data=data))
