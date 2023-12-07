from odoo import fields, models


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    stock_id = fields.Many2one('stock.picking', setring="Stock", help="Stock")

    def process(self):
        pickings_to_do = self.env['stock.picking']
        pickings_not_to_do = self.env['stock.picking']
        for line in self.backorder_confirmation_line_ids:
            if line.to_backorder is True:
                pickings_to_do |= line.picking_id
            else:
                pickings_not_to_do |= line.picking_id
        pickings_to_validate = self.env.context.get(
            'button_validate_picking_ids')
        if pickings_to_validate:
            pickings_to_validate = self.env['stock.picking'].browse(
                pickings_to_validate).with_context(skip_backorder=True)
            if pickings_not_to_do:
                self._check_less_quantities_than_expected(pickings_not_to_do)
                pickings_to_validate = pickings_to_validate.with_context(
                    picking_ids_not_to_backorder=pickings_not_to_do.ids)
            result_validate = pickings_to_validate.button_validate()
            result_transfer = ''
            if not pickings_to_validate.auto_generated:
                result_transfer = pickings_to_validate.create_intercompany_transfer()
                pickings_to_validate.write(
                    {'is_backorder_button_clicked': True})
            return result_validate, result_transfer
        return True

    def process_cancel_backorder(self):
        pickings_to_validate_ids = self.env.context.get(
            'button_validate_picking_ids')
        if pickings_to_validate_ids:
            pickings_to_validate = self.env['stock.picking'].browse(
                pickings_to_validate_ids)
            self._check_less_quantities_than_expected(pickings_to_validate)
            result_validate = pickings_to_validate.with_context(
                skip_backorder=True,
                picking_ids_not_to_backorder=self.pick_ids.ids).button_validate()
            result_transfer = ''
            if not pickings_to_validate.auto_generated:
                result_transfer = pickings_to_validate.create_intercompany_transfer()
            return result_validate, result_transfer
        return True
