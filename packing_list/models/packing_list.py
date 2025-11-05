from odoo import models, fields, api
from odoo.tools import unique


class StockMove(models.Model):
    _inherit = 'stock.move'

    pack_number = fields.Integer(string="Package Number")
    remarks = fields.Char('Remarks')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    product_ref = fields.Boolean(string="Product Reference")
    total_package = fields.Integer(compute="_total_packages", string="Packages")

    @api.multi
    def print_pdf_report(self):
        records = self.env['stock.picking'].search([('id', '=', self.id)])

        if records:
            return self.env.ref('packing_list.action_packing_list_report').report_action(records, config=False)

    def _total_packages(self):
        rec = self.env['stock.move'].search([('picking_id', '=', self.id)]).mapped('pack_number')
        test = list(unique(rec))
        self.total_package = len(test)
