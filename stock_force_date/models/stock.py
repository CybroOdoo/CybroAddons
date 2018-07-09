# -*- coding: utf-8 -*-
import time
import logging
from datetime import datetime
from collections import defaultdict
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = "stock.picking"

    force_date = fields.Datetime('Force Date')


class Quant(models.Model):
    _inherit = "stock.quant"

    @api.model
    def quants_move(self, quants, move, location_to, location_from=False, lot_id=False, owner_id=False,
                    src_package_id=False, dest_package_id=False, entire_pack=False):
        """Moves all given stock.quant in the given destination location.  Unreserve from current move.
        :param quants: list of tuple(browse record(stock.quant) or None, quantity to move)
        :param move: browse record (stock.move)
        :param location_to: browse record (stock.location) depicting where the quants have to be moved
        :param location_from: optional browse record (stock.location) explaining where the quant has to be taken
                              (may differ from the move source location in case a removal strategy applied).
                              This parameter is only used to pass to _quant_create_from_move if a negative quant must be created
        :param lot_id: ID of the lot that must be set on the quants to move
        :param owner_id: ID of the partner that must own the quants to move
        :param src_package_id: ID of the package that contains the quants to move
        :param dest_package_id: ID of the package that must be set on the moved quant
        """
        # TDE CLEANME: use ids + quantities dict
        if location_to.usage == 'view':
            raise UserError(_('You cannot move to a location of type view %s.') % (location_to.name))

        quants_reconcile_sudo = self.env['stock.quant'].sudo()
        quants_move_sudo = self.env['stock.quant'].sudo()
        check_lot = False
        for quant, qty in quants:
            if not quant:
                # If quant is None, we will create a quant to move (and potentially a negative counterpart too)
                quant = self._quant_create_from_move(
                    qty, move, lot_id=lot_id, owner_id=owner_id, src_package_id=src_package_id,
                    dest_package_id=dest_package_id, force_location_from=location_from, force_location_to=location_to)
                if move.picking_id.force_date:
                    quant.write({'in_date': move.picking_id.force_date})
                check_lot = True
            else:
                _logger.info(quant)
                quant._quant_split(qty)
                _logger.info(quant)
                quants_move_sudo |= quant
            quants_reconcile_sudo |= quant

        if quants_move_sudo:
            moves_recompute = quants_move_sudo.filtered(lambda self: self.reservation_id != move).mapped(
                'reservation_id')
            quants_move_sudo._quant_update_from_move(move, location_to, dest_package_id, lot_id=lot_id,
                                                     entire_pack=entire_pack)
            moves_recompute.recalculate_move_state()

        if location_to.usage == 'internal':
            # Do manual search for quant to avoid full table scan (order by id)
            self._cr.execute("""
                SELECT 0 FROM stock_quant, stock_location WHERE product_id = %s AND stock_location.id = stock_quant.location_id AND
                ((stock_location.parent_left >= %s AND stock_location.parent_left < %s) OR stock_location.id = %s) AND qty < 0.0 LIMIT 1
            """, (move.product_id.id, location_to.parent_left, location_to.parent_right, location_to.id))
            if self._cr.fetchone():
                quants_reconcile_sudo._quant_reconcile_negative(move)

        # In case of serial tracking, check if the product does not exist somewhere internally already
        # Checking that a positive quant already exists in an internal location is too restrictive.
        # Indeed, if a warehouse is configured with several steps (e.g. "Pick + Pack + Ship") and
        # one step is forced (creates a quant of qty = -1.0), it is not possible afterwards to
        # correct the inventory unless the product leaves the stock.
        picking_type = move.picking_id and move.picking_id.picking_type_id or False
        if check_lot and lot_id and move.product_id.tracking == 'serial' and (
            not picking_type or (picking_type.use_create_lots or picking_type.use_existing_lots)):
            other_quants = self.search([('product_id', '=', move.product_id.id), ('lot_id', '=', lot_id),
                                        ('qty', '>', 0.0), ('location_id.usage', '=', 'internal')])
            if other_quants:
                # We raise an error if:
                # - the total quantity is strictly larger than 1.0
                # - there are more than one negative quant, to avoid situations where the user would
                #   force the quantity at several steps of the process
                if sum(other_quants.mapped('qty')) > 1.0 or len([q for q in other_quants.mapped('qty') if q < 0]) > 1:
                    lot_name = self.env['stock.production.lot'].browse(lot_id).name
                    raise UserError(_('The serial number %s is already in stock.') % lot_name + _(
                        "Otherwise make sure the right stock/owner is set."))

    @api.multi
    def _quant_update_from_move(self, move, location_dest_id, dest_package_id, lot_id=False, entire_pack=False):
        super(Quant, self)._quant_update_from_move(move, location_dest_id, dest_package_id, lot_id=False,
                                                   entire_pack=False)
        if move.picking_id.force_date:
            self.write({'in_date': move.picking_id.force_date})

    def _create_account_move_line(self, move, credit_account_id, debit_account_id, journal_id):
        # group quants by cost
        quant_cost_qty = defaultdict(lambda: 0.0)
        for quant in self:
            quant_cost_qty[quant.cost] += quant.qty
        AccountMove = self.env['account.move']
        for cost, qty in quant_cost_qty.iteritems():
            move_lines = move._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id)
            if move_lines:
                if move.picking_id.force_date:
                    date = datetime.strptime(move.picking_id.force_date, '%Y-%m-%d %H:%M:%S')
                else:
                    date = self._context.get('force_period_date', fields.Date.context_today(self))
                new_account_move = AccountMove.create({
                    'journal_id': journal_id,
                    'line_ids': move_lines,
                    'date': date,
                    'ref': move.picking_id.name})
                new_account_move.post()


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.multi
    def action_done(self):
        """ Process completely the moves given and if all moves are done, it will finish the picking. """
        self.filtered(lambda move: move.state == 'draft').action_confirm()

        Uom = self.env['product.uom']
        Quant = self.env['stock.quant']

        pickings = self.env['stock.picking']
        procurements = self.env['procurement.order']
        operations = self.env['stock.pack.operation']

        remaining_move_qty = {}

        for move in self:
            if move.picking_id:
                pickings |= move.picking_id
            remaining_move_qty[move.id] = move.product_qty
            for link in move.linked_move_operation_ids:
                operations |= link.operation_id
                pickings |= link.operation_id.picking_id

        # Sort operations according to entire packages first, then package + lot, package only, lot only
        operations = operations.sorted(key=lambda x: ((x.package_id and not x.product_id) and -4 or 0) + (x.package_id and -2 or 0) + (x.pack_lot_ids and -1 or 0))

        for operation in operations:

            # product given: result put immediately in the result package (if False: without package)
            # but if pack moved entirely, quants should not be written anything for the destination package
            quant_dest_package_id = operation.product_id and operation.result_package_id.id or False
            entire_pack = not operation.product_id and True or False

            # compute quantities for each lot + check quantities match
            lot_quantities = dict((pack_lot.lot_id.id, operation.product_uom_id._compute_quantity(pack_lot.qty, operation.product_id.uom_id)
            ) for pack_lot in operation.pack_lot_ids)

            qty = operation.product_qty
            if operation.product_uom_id and operation.product_uom_id != operation.product_id.uom_id:
                qty = operation.product_uom_id._compute_quantity(qty, operation.product_id.uom_id)
            if operation.pack_lot_ids and float_compare(sum(lot_quantities.values()), qty, precision_rounding=operation.product_id.uom_id.rounding) != 0.0:
                raise UserError(_('You have a difference between the quantity on the operation and the quantities specified for the lots. '))

            quants_taken = []
            false_quants = []
            lot_move_qty = {}

            prout_move_qty = {}
            for link in operation.linked_move_operation_ids:
                prout_move_qty[link.move_id] = prout_move_qty.get(link.move_id, 0.0) + link.qty

            # Process every move only once for every pack operation
            for move in prout_move_qty.keys():
                # TDE FIXME: do in batch ?
                move.check_tracking(operation)

                # TDE FIXME: I bet the message error is wrong
                if not remaining_move_qty.get(move.id):
                    raise UserError(_("The roundings of your unit of measure %s on the move vs. %s on the product don't allow to do these operations or you are not transferring the picking at once. ") % (move.product_uom.name, move.product_id.uom_id.name))

                if not operation.pack_lot_ids:
                    preferred_domain_list = [[('reservation_id', '=', move.id)], [('reservation_id', '=', False)], ['&', ('reservation_id', '!=', move.id), ('reservation_id', '!=', False)]]
                    quants = Quant.quants_get_preferred_domain(
                        prout_move_qty[move], move, ops=operation, domain=[('qty', '>', 0)],
                        preferred_domain_list=preferred_domain_list)
                    Quant.quants_move(quants, move, operation.location_dest_id, location_from=operation.location_id,
                                      lot_id=False, owner_id=operation.owner_id.id, src_package_id=operation.package_id.id,
                                      dest_package_id=quant_dest_package_id, entire_pack=entire_pack)
                else:
                    # Check what you can do with reserved quants already
                    qty_on_link = prout_move_qty[move]
                    rounding = operation.product_id.uom_id.rounding
                    for reserved_quant in move.reserved_quant_ids:
                        if (reserved_quant.owner_id.id != operation.owner_id.id) or (reserved_quant.location_id.id != operation.location_id.id) or \
                                (reserved_quant.package_id.id != operation.package_id.id):
                            continue
                        if not reserved_quant.lot_id:
                            false_quants += [reserved_quant]
                        elif float_compare(lot_quantities.get(reserved_quant.lot_id.id, 0), 0, precision_rounding=rounding) > 0:
                            if float_compare(lot_quantities[reserved_quant.lot_id.id], reserved_quant.qty, precision_rounding=rounding) >= 0:
                                lot_quantities[reserved_quant.lot_id.id] -= reserved_quant.qty
                                quants_taken += [(reserved_quant, reserved_quant.qty)]
                                qty_on_link -= reserved_quant.qty
                            else:
                                quants_taken += [(reserved_quant, lot_quantities[reserved_quant.lot_id.id])]
                                lot_quantities[reserved_quant.lot_id.id] = 0
                                qty_on_link -= lot_quantities[reserved_quant.lot_id.id]
                    lot_move_qty[move.id] = qty_on_link

                remaining_move_qty[move.id] -= prout_move_qty[move]

            # Handle lots separately
            if operation.pack_lot_ids:
                # TDE FIXME: fix call to move_quants_by_lot to ease understanding
                self._move_quants_by_lot(operation, lot_quantities, quants_taken, false_quants, lot_move_qty, quant_dest_package_id)

            # Handle pack in pack
            if not operation.product_id and operation.package_id and operation.result_package_id.id != operation.package_id.parent_id.id:
                operation.package_id.sudo().write({'parent_id': operation.result_package_id.id})

        # Check for remaining qtys and unreserve/check move_dest_id in
        move_dest_ids = set()
        for move in self:
            if float_compare(remaining_move_qty[move.id], 0, precision_rounding=move.product_id.uom_id.rounding) > 0:  # In case no pack operations in picking
                move.check_tracking(False)  # TDE: do in batch ? redone ? check this

                preferred_domain_list = [[('reservation_id', '=', move.id)], [('reservation_id', '=', False)], ['&', ('reservation_id', '!=', move.id), ('reservation_id', '!=', False)]]
                quants = Quant.quants_get_preferred_domain(
                    remaining_move_qty[move.id], move, domain=[('qty', '>', 0)],
                    preferred_domain_list=preferred_domain_list)
                Quant.quants_move(
                    quants, move, move.location_dest_id,
                    lot_id=move.restrict_lot_id.id, owner_id=move.restrict_partner_id.id)

            # If the move has a destination, add it to the list to reserve
            if move.move_dest_id and move.move_dest_id.state in ('waiting', 'confirmed'):
                move_dest_ids.add(move.move_dest_id.id)

            if move.procurement_id:
                procurements |= move.procurement_id

            # unreserve the quants and make them available for other operations/moves
            move.quants_unreserve()

        # Check the packages have been placed in the correct locations
        self.mapped('quant_ids').filtered(lambda quant: quant.package_id and quant.qty > 0).mapped('package_id')._check_location_constraint()

        # set the move as done
        # setting force_date into stock moves
        f_date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        for move in self:
            if move.picking_id.force_date:
                f_date = move.picking_id.force_date
        self.write({'state': 'done', 'date': f_date})
        # self.write({'state': 'done', 'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
        procurements.check()
        # assign destination moves
        if move_dest_ids:
            # TDE FIXME: record setise me
            self.browse(list(move_dest_ids)).action_assign()

        pickings.filtered(lambda picking: picking.state == 'done' and not picking.date_done).write(
            {'date_done': f_date})
        # pickings.filtered(lambda picking: picking.state == 'done' and not picking.date_done).write({'date_done': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})

        return True
