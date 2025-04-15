# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anfas Faisal K (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
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
from odoo import api, models
from datetime import datetime, timedelta


class FleetDashboard(models.Model):
    """
    Model for the Fleet Dashboard, providing various statistics and data
    related to the fleet vehicles, contracts, and invoices.
    """
    _name = 'fleet.dashboard'
    _description = 'Fleet Dashboard'

    @api.model
    def get_datas(self):
        """
        Retrieves overall statistics related to fleet vehicles, contracts,
        and invoices.
        """
        total_vehicles = self.env['fleet.vehicle'].search_count([])
        operational_vehicles = self.env['fleet.vehicle'].search_count(
            [('status', '=', 'operational')])
        maintenance_vehicles = self.env['fleet.vehicle'].search_count(
            [('status', '=', 'undermaintenance')])
        all_invoices = self.env['account.move'].search_count(
            [('vehicle_rental_id', '!=', False)])
        pending_invoices = self.env['account.move'].search_count([
            ('vehicle_rental_id', '!=', False),
            ('state', '=', 'posted'),
            ('payment_state', '!=', 'paid')
        ])
        total_contracts = self.env['fleet.rental.contract'].search_count([])
        total_contract_working = self.env[
            'fleet.rental.contract'].search_count(
            [('state', '=', 'in_progress')])
        total_contract_returned = self.env[
            'fleet.rental.contract'].search_count(
            [('state', '=', 'return')])
        total_contract_cancel = self.env['fleet.rental.contract'].search_count(
            [('state', '=', 'cancel')])

        return {
            'total_vehicles': total_vehicles,
            'total_contracts': total_contracts,
            'total_contract_working': total_contract_working,
            'total_contract_return': total_contract_returned,
            'total_contract_cancel': total_contract_cancel,
            'operational': operational_vehicles,
            'under_maintenance': maintenance_vehicles,
            'all_customers': self.env['res.partner'].search_count([]),
            'all_invoices': all_invoices,
            'pending_invoices': pending_invoices,
        }

    @api.model
    def get_monthly_contract_invoices(self):
        """
        Retrieves the count of posted invoices for each month of the
        current year related to vehicle rentals.
        """
        current_year = datetime.now().year
        data = []
        labels = ['January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November',
                  'December']

        for month in range(1, 13):
            start_date = datetime(current_year, month, 1)
            end_date = (start_date + timedelta(days=32)).replace(
                day=1) - timedelta(days=1)

            invoice_count = self.env['account.move'].search_count([
                ('vehicle_rental_id', '!=', False),
                ('invoice_date', '>=', start_date),
                ('invoice_date', '<=', end_date),
                ('state', '=', 'posted')
            ])
            data.append(invoice_count)
        return {
            'labels': labels,
            'data': data
        }
