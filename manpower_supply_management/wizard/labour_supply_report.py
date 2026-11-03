# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import fields, models


class LabourSupplyReport(models.TransientModel):
    """
    Get report about contract through this class
    """
    _name = 'labour.supply.report'
    _description = 'Get PDF Report'

    filter = fields.Selection(default="customer_wise",
                              selection=[('customer_wise', 'Customer Wise'),
                                         ('state_wise', 'State Wise')],
                              help="Field to choose filter of report")
    customer_id = fields.Many2one('res.partner',
                                  string="Choose customer",
                                  help="Field to choose customer for report")
    state_id = fields.Selection([('draft', 'Draft'), ('ready', 'Ready'),
                                 ('confirmed', 'Confirmed'),
                                 ('invoiced', 'Invoiced'),
                                 ('expired', 'Expired')],
                                default="ready",
                                help="Field to specify state of report")
    from_date = fields.Date(string="From date",
                            help="Field to choose start date of report")
    to_date = fields.Date(string="To date",
                          help="Field to end date filter of report")

    def _get_report_domain(self):
        """
        Summary:
           Build the search domain from the wizard filters. Every filter is
           added independently, so a date filter works with or without a
           customer or state, and with or without the other date.
        return:
           domain for labour.supply
        """
        self.ensure_one()
        domain = []
        if self.filter == 'customer_wise' and self.customer_id:
            domain.append(('customer_id', '=', self.customer_id.id))
        if self.filter == 'state_wise' and self.state_id:
            domain.append(('state', '=', self.state_id))
        if self.from_date:
            domain.append(('from_date', '>=', self.from_date))
        if self.to_date:
            domain.append(('to_date', '<=', self.to_date))
        return domain

    def action_print_pdf(self):
        """
        Summary:
           function to print pdf
        return:
           pdf report
        """
        self.ensure_one()
        contracts = self.env['labour.supply'].search(
            self._get_report_domain())
        datas = [{
            'name': contract.customer_id.name,
            'sequence_number': contract.sequence_number,
            'state': contract.state,
            'from_date': contract.from_date,
            'to_date': contract.to_date,
            'total_amount': contract.total_amount,
        } for contract in contracts]
        data = {
            'form': self.read()[0],
            'datas': datas,
            'from_date': self.from_date,
            'to_date': self.to_date,
        }
        if self.filter == 'customer_wise':
            data['customer_id'] = self.customer_id.name
            report = self.env.ref(
                'manpower_supply_management.action_labour_supply_report')
        else:
            data['state_id'] = self.state_id
            report = self.env.ref(
                'manpower_supply_management.'
                'action_labour_supply_report_second')
        return report.report_action(None, data=data)
