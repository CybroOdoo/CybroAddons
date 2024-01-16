# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ranjith R(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###########################################################################
from odoo import fields, models


class LabourSupplyReport(models.TransientModel):
    """
    Get report about contract through this class
    """
    _name = 'labour.supply.report'
    _description = 'Get Pdf Report'

    filter = fields.Selection(string="Filter",
                              default="customer_wise",
                              selection=[('customer_wise', 'Customer wise'),
                                         ('state_wise', 'State wise')],
                              help="Field to choose filter of report")
    customer_id = fields.Many2one('res.partner',
                                  string="Choose customer",
                                  help="Field to choose customer for report")
    state_id = fields.Selection([('draft', 'Draft'), ('ready', 'Ready'),
                                 ('confirmed', 'Confirmed'),
                                 ('invoiced', 'Invoiced'),
                                 ('expired', 'Expired')],
                                default="ready", string="State",
                                help="Field to specify state of report")
    from_date = fields.Date(string="From date",
                            help="Field to choose start date of report")
    to_date = fields.Date(string="To date",
                          help="Field to end date filter of report")

    def action_print_pdf(self):
        """
        Summary:
           function to print pdf
        return:
           pdf report
        """
        if self.filter == 'customer_wise':
            query = """select res_partner.name,labour_supply.sequence_number,
            labour_supply.state,labour_supply.from_date,labour_supply.to_date,
            labour_supply.total_amount from labour_supply
            inner join res_partner on res_partner.id = labour_supply.customer_id
            """
            if self.customer_id:
                query += f"""where res_partner.id = {self.customer_id.id:d} """
            if self.from_date:
                query += f""" and labour_supply.from_date >= '
                              {self.from_date}' """
            if self.from_date:
                query += f""" and labour_supply.to_date <= '{self.to_date}' """
            self.env.cr.execute(query)
            datas = self.env.cr.dictfetchall()

            data = {
                'form': self.read()[0],
                'datas': datas,
                'customer_id': self.customer_id.name,
                'from_date': self.from_date,
                'to_date': self.to_date
            }
            return self.env.ref(
                'manpower_supply_management.action_labour_supply_report').report_action(
                None, data=data)
        if self.filter == 'state_wise':
            query = """select * from labour_supply
                   """
            if self.state_id:
                query += f"""where labour_supply.state = '{self.state_id}' """
            if self.from_date:
                query += (f" and labour_supply.from_date >= \n"
                          f"                          '{self.from_date}' ")
            if self.from_date:
                query += f""" and labour_supply.to_date <= '{self.to_date}' """
            self.env.cr.execute(query)
            datas = self.env.cr.dictfetchall()
            data = {
                'form': self.read()[0],
                'datas': datas,
                'state_id': self.state_id,
                'from_date': self.from_date,
                'to_date': self.to_date
            }
            return self.env.ref(
                'manpower_supply_management.action_labour_supply_report_second').report_action(
                None, data=data)
