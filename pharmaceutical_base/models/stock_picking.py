# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class StockPicking(models.Model):
    """Extends stock.picking to enforce GMP lot quarantine on goods receipt."""
    _inherit = 'stock.picking'

    def _action_done(self):
        """Force quarantine status on all lots received via incoming shipments."""
        if not self.env.context.get('pharma_qa_disposition'):
            for picking in self:
                if picking.picking_type_id.code != 'incoming':
                    self._check_pharma_lot_status(picking)

        for picking in self:
            company = picking.company_id or self.env.company
            if company.pharma_enforce_storage_class:
                self._check_pharma_storage_class(picking)

        result = super()._action_done()

        for picking in self:
            if picking.picking_type_id.code == 'incoming':
                lines = self.env['stock.move.line'].search([('picking_id', '=', picking.id), ('state', '=', 'done')])
                lots = lines.mapped('lot_id')
                lots_to_quarantine = lots.filtered(
                    lambda l: not l.lot_status or l.lot_status == 'quarantine'
                )
                if lots_to_quarantine:
                    lots_to_quarantine.write({'lot_status': 'quarantine'})
                    msg = _('GMP: %d lot(s) automatically set to Quarantine on receipt validation.') % len(lots_to_quarantine)
                    picking.message_post(body=msg)
        return result

    @staticmethod
    def _check_pharma_lot_status(picking):
        """Block picking lots whose pharma status is not approved or released."""
        BLOCKED = {'quarantine', 'rejected', 'on_hold', 'recalled'}
        STATUS_LABEL = {
            'quarantine': 'Quarantine',
            'rejected':   'Rejected',
            'on_hold':    'On Hold',
            'recalled':   'Recalled',
        }
        for line in picking.move_line_ids:
            lot = line.lot_id
            if lot and lot.lot_status in BLOCKED:
                raise UserError(_(
                    'GMP Violation: Lot/Batch \'%(lot)s\' (%(product)s) '
                    'has status \'%(status)s\' and cannot be used in this operation.\n\n'
                    'Release the lot from the Quarantine Queue before proceeding.',
                    lot=lot.name,
                    product=lot.product_id.display_name,
                    status=STATUS_LABEL.get(lot.lot_status, lot.lot_status),
                ))

    @staticmethod
    def _check_pharma_storage_class(picking):
        """Block move lines landing a classified material in a wrong storage area."""
        for line in picking.move_line_ids:
            required = line.product_id.storage_category_id
            destination = line.location_dest_id
            if not required or destination.usage != 'internal':
                continue
            if required not in destination._pharma_storage_categories():
                raise UserError(_(
                    "GMP Violation: %(product)s requires storage class "
                    "'%(required)s', but '%(location)s' does not provide it.\n\n"
                    "Move the line to a location under the %(required)s area, or "
                    "correct the Storage Class on the product.",
                    product=line.product_id.display_name,
                    required=required.name,
                    location=destination.complete_name,
                ))
