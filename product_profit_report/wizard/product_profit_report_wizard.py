# -*- coding: utf-8 -*-
import datetime
from odoo import models, fields, api


class ProductProfitReport(models.TransientModel):
    _name = "product_profit_report.report"
    _description = 'Product Profit Report'

    @api.model
    def _get_from_date(self):
        company = self.env.user.company_id
        current_date = datetime.date.today()
        from_date = company.compute_fiscalyear_dates(current_date)['date_from']
        return from_date

    from_date = fields.Date(string='From Date', default=_get_from_date, required=True)
    to_date = fields.Date(string='To Date', default=fields.Date.context_today, required=True)
    company = fields.Many2one('res.company', string='Company', required=True,
                              default=lambda self: self.env.user.company_id.id)
    categ_id = fields.Many2one('product.category', string='Product Category', required=False)
    product_id = fields.Many2one('product.product', string='Product', required=False,)

    @api.onchange('categ_id')
    def _onchange_category_products(self):
        if self.categ_id:
            products = self.env['product.product'].search([('categ_id', '=', self.categ_id.id)])
            return {
                'domain': {'product_id': [('id', 'in', products.ids)]}
            }

    def print_pdf_report(self, data):
        data = {}
        data['form'] = {}
        data['form'].update(self.read([])[0])
        return self.env.ref('product_profit_report.action_product_profit_report_pdf').with_context(
            landscape=True).report_action(self, data=data)
