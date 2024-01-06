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


class ScrapManagementReport(models.TransientModel):
    """Get report about contract   """
    _name = 'scrap.management.report'
    _description = 'Report of Scrap Management'

    filter = fields.Selection(
        default="product_wise", selection=[('product_wise', 'Product Wise'),
                                           ('state_wise', 'State Wise')],
        help="field to choose filter of report", string="Based On")
    product_ids = fields.Many2many('product.product',
                                   string="Product",
                                   help="Field to choose product for report")
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done'),
                              ('confirm', 'Confirm')],
                             default="done", string="State",
                             help="Field to specify state of report")
    from_date = fields.Date(string="Start date",
                            help="Field to choose start date of report")
    to_date = fields.Date(string="End date",
                          help="Field to end date filter of report")

    def action_print_pdf(self):
        """
        Summary:
           function to print pdf
        Return:
           pdf report
        """
        if self.filter == 'product_wise':
            query = """SELECT scrap_management.scrap_management_number,
            scrap_management.scrap_order_id,
            product_template.name->> 'en_US'AS product,
            scrap_management.state,stock_scrap.product_id,scrap_management.date,
            stock_scrap.name FROM scrap_management
            inner join stock_scrap on
            scrap_management.scrap_order_id= stock_scrap.id
            inner join product_product on 
            product_product.id=stock_scrap.product_id
            inner join product_template on 
            product_template.id=product_product.product_tmpl_id
            """
            lst = []
            for product in self.product_ids:
                lst.append(product.id)
            if self.product_ids:
                lst.append(0)
                query += f""" where stock_scrap.product_id in {tuple(lst)}"""
            if self.from_date:
                query += f""" and scrap_management.date >= '{self.from_date}' """
            if self.from_date:
                query += f""" and scrap_management.date <= '{self.to_date}' """
            self.env.cr.execute(query)
            datas = self.env.cr.dictfetchall()
            data = {
                'form': self.read()[0],
                'datas': datas,
                'from_date': self.from_date,
                'to_date': self.to_date
            }
            return self.env.ref(
                'company_scrap_management'
                '.action_scrap_management_product_wise').report_action(
                None,
                data=data)
        if self.filter == 'state_wise':
            query = """SELECT scrap_management.scrap_management_number,
            stock_scrap.name,scrap_management.scrap_order_id,
            scrap_management.state,stock_scrap.product_id,stock_scrap.name,
            scrap_management.date FROM scrap_management
            inner join stock_scrap 
            on scrap_management.scrap_order_id= stock_scrap.id
            """
            if self.state:
                query += f"""where scrap_management.state = '{self.state}' """
            if self.from_date:
                query += f""" and scrap_management.date >= '{self.from_date}' """
            if self.from_date:
                query += f""" and scrap_management.date <= '{self.to_date}' """
            self.env.cr.execute(query)
            datas = self.env.cr.dictfetchall()
            data = {
                'form': self.read()[0],
                'datas': datas,
                'state': self.state,
                'from_date': self.from_date,
                'to_date': self.to_date
            }
            return self.env.ref(
                'company_scrap_management'
                '.action_scrap_management_state_wise').report_action(None,
                                                                     data=data)
