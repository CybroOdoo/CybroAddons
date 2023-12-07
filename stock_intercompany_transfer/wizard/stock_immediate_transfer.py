from odoo import models, _
from odoo.exceptions import UserError


class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'

    def process(self):
        pickings_to_do = self.env['stock.picking']
        pickings_not_to_do = self.env['stock.picking']
        for line in self.immediate_transfer_line_ids:
            if line.to_immediate is True:
                pickings_to_do |= line.picking_id
            else:
                pickings_not_to_do |= line.picking_id

        for picking in pickings_to_do:
            # If still in draft => confirm and assign
            if picking.state == 'draft':
                picking.action_confirm()
                if picking.state != 'assigned':
                    picking.action_assign()
                    if picking.state != 'assigned':
                        raise UserError(
                            _("Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
            picking.move_ids._set_quantities_to_reservation()
        pickings_to_validate = self.env.context.get(
            'button_validate_picking_ids')
        if pickings_to_validate:
            pickings_to_validate = self.env['stock.picking'].browse(
                pickings_to_validate)
            pickings_to_validate = pickings_to_validate - pickings_not_to_do
            pickings_to_validate.write({'state': 'done'})
            if not pickings_to_validate.auto_generated:
                return pickings_to_validate.with_context(
                    skip_immediate=True).create_intercompany_transfer()
        return True
