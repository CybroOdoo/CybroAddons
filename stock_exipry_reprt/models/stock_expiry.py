# -*- coding: utf-8 -*-
from odoo import fields,api,models


class StockExpiry(models.TransientModel):

    _name = 'stockz.expiry'

    report_dayz = fields.Char(string='Generate Report For(days)',required=True)
    check = fields.Boolean(string='Location Wise Report', default=False,
                           help="Enable this For Printing the report of all locations")
    int_location = fields.Many2one('stock.location', string='Location', required=True)

    @api.multi
    def print_report(self):
        data = {'report_dayz': self.report_dayz, 'check': self.check, 'int_location': self.int_location.id}
        return self.env.ref('stock_exipry_reprt.stock_expiry_pdf').report_action(self, data=data)
