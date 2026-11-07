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


class ScrapManagementReport(models.TransientModel):
    """This class defining model for the wizard for printing scrap management
    report."""
    _name = 'scrap.management.report'
    _description = 'Report of Scrap Management'

    filter = fields.Selection(
        default="product_wise", selection=[('product_wise', 'Product Wise'),
                                           ('state_wise', 'State Wise')],
        help="Field to choose filter of report", string="Based On")
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
        """Print PDF report based on wizard filters."""
        self.ensure_one()
        if self.filter == 'product_wise':
            domain = []
            if self.product_ids:
                domain.append(('product_id', 'in', self.product_ids.ids))
            if self.from_date:
                domain.append(('date', '>=', self.from_date))
            if self.to_date:
                domain.append(('date', '<=', self.to_date))

            records = self.env['scrap.management'].search(domain)
            datas = [{
                'scrap_management_number': rec.scrap_management_number,
                'scrap_order_id': rec.scrap_order_id.id,
                'product': rec.product_id.display_name,
                'state': dict(rec._fields['state'].selection).get(rec.state, rec.state),
                'product_id': rec.product_id.id,
                'date': rec.date,
                'name': rec.scrap_order_id.reference or '',
            } for rec in records]

            data = {
                'form': self.read()[0],
                'datas': datas,
                'from_date': self.from_date,
                'to_date': self.to_date,
            }
            return self.env.ref(
                'company_scrap_management'
                '.action_scrap_management_product_wise'
            ).report_action(None, data=data, config=False)

        if self.filter == 'state_wise':
            domain = []
            if self.state:
                domain.append(('state', '=', self.state))
            if self.from_date:
                domain.append(('date', '>=', self.from_date))
            if self.to_date:
                domain.append(('date', '<=', self.to_date))

            records = self.env['scrap.management'].search(domain)
            datas = [{
                'scrap_management_number': rec.scrap_management_number,
                'name': rec.scrap_order_id.reference or '',
                'scrap_order_id': rec.scrap_order_id.id,
                'state': dict(rec._fields['state'].selection).get(rec.state, rec.state),
                'product_id': rec.product_id.id,
                'date': rec.date,
            } for rec in records]

            data = {
                'form': self.read()[0],
                'datas': datas,
                'state': self.state,
                'from_date': self.from_date,
                'to_date': self.to_date,
            }
            return self.env.ref(
                'company_scrap_management'
                '.action_scrap_management_state_wise'
            ).report_action(None, data=data, config=False)
