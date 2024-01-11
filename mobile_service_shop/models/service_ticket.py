# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu KP S (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import models, api


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
