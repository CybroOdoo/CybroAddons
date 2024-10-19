# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Jumana Jabin MP (odoo@cybrosys.com)
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
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, models


class MobileServiceTicket(models.AbstractModel):
    """Mobile service ticket report abstract model"""
    _name = 'report.mobile_service_shop.mobile_service_ticket_template'

    @api.model
    def _get_report_values(self, docids, data):
        """Returns the data file for the report"""
        terms = self.env['terms.conditions'].search([])
        return {
            'date_today': data['date_today'],
            'date_request': data['date_request'],
            'date_return': data['date_return'],
            'sev_id': data['sev_id'],
            'imei_no': data['imei_no'],
            'technician': data['technician'],
            'complaint_types': data['complaint_types'],
            'complaint_description': data['complaint_description'],
            'mobile_brand': data['mobile_brand'],
            'model_name': data['model_name'],
            'customer_name': data['customer_name'],
            'warranty': data['warranty'],
            'terms': terms}
