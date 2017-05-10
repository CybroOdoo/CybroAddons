from openerp import models, fields, api


class StockReport(models.TransientModel):
    _name = "wizard.stock.history"
    _description = "Current Stock History"

    warehouse = fields.Many2many('stock.warehouse', 'wh_wiz_rel', 'wh', 'wiz', string='Warehouse', required=True)
    category = fields.Many2many('product.category', 'categ_wiz_rel', 'categ', 'wiz', string='Warehouse')

    @api.multi
    def export_xls(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'product.product'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        if context.get('xls_export'):
            return {'type': 'ir.actions.report.xml',
                    'report_name': 'export_stockinfo_xls.stock_report_xls.xlsx',
                    'datas': datas,
                    'name': 'Current Stock'
                    }
