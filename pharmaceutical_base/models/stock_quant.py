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

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class StockQuant(models.Model):
    """Extends stock.quant to support GMP Quarantine Queue operations."""
    _inherit = 'stock.quant'

    has_incoming_qc = fields.Boolean(help='Specifies the Has Incoming Qc for this record.',
        string='Has Incoming QC',
        compute='_compute_has_incoming_qc',
    )

    qc_test_order_count = fields.Integer(help='Specifies the Qc Test Order Count for this record.',
        string='QC Test Orders',
        compute='_compute_qc_test_order_count',
    )

    move_line_count = fields.Integer(help='Specifies the Move Line Count for this record.',
        string='Stock Moves',
        compute='_compute_move_line_count',
    )

    @api.depends('lot_id', 'product_id')
    def _compute_move_line_count(self):
        """Executes the _compute_move_line_count operation."""
        for quant in self:
            quant.move_line_count = self.env['stock.move.line'].search_count(
                quant._pharma_move_line_domain())

    @api.depends('lot_id', 'product_id')
    def _compute_has_incoming_qc(self):
        """Check if this quant's lot/batch has an existing incoming QC test order."""
        for quant in self:
            product_tmpl = quant.product_id.product_tmpl_id
            if not product_tmpl:
                quant.has_incoming_qc = False
                continue
            domain = [('product_id', '=', product_tmpl.id)]
            if quant.lot_id:
                domain.append(('lot_id', '=', quant.lot_id.id))
            existing = self.env['pharma.qc.test.order'].search_count(domain)
            quant.has_incoming_qc = bool(existing)

    @api.depends('lot_id', 'product_id')
    def _compute_qc_test_order_count(self):
        """Calculates the number of QC Test Orders for this quant's lot/batch."""
        for quant in self:
            product_tmpl = quant.product_id.product_tmpl_id
            if not product_tmpl:
                quant.qc_test_order_count = 0
                continue
            domain = [('product_id', '=', product_tmpl.id)]
            if quant.lot_id:
                domain.append(('lot_id', '=', quant.lot_id.id))
            quant.qc_test_order_count = self.env['pharma.qc.test.order'].search_count(domain)

    def action_view_qc_test_orders(self):
        """Open the QC Test Orders linked to this quant's batch/lot."""
        self.ensure_one()
        product_tmpl = self.product_id.product_tmpl_id
        action = self.env['ir.actions.act_window']._for_xml_id(
            'pharmaceutical_base.pharma_qc_test_order')
        domain = [('product_id', '=', product_tmpl.id)]
        if self.lot_id:
            domain.append(('lot_id', '=', self.lot_id.id))
        action['domain'] = domain
        action['context'] = {
            'default_product_id': product_tmpl.id,
            'default_lot_id': self.lot_id.id if self.lot_id else False,
            'default_stage': 'incoming',
        }
        orders = self.env['pharma.qc.test.order'].search(domain)
        if len(orders) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = orders.id
        return action

    def action_quant_create_qc_test(self):
        """Creates QC Test Orders for separate batch lots in quarantine."""
        created_count = 0
        for quant in self:
            lot = quant.lot_id
            if not lot:
                continue
            product_tmpl = quant.product_id.product_tmpl_id
            domain = [('product_id', '=', product_tmpl.id), ('lot_id', '=', lot.id)]
            existing_order = self.env['pharma.qc.test.order'].search_count(domain)
            if existing_order:
                continue

            self.env['pharma.qc.test.order'].create({
                'product_id': product_tmpl.id,
                'lot_id': lot.id,
                'stage': 'incoming'
            })
            created_count += 1

        if created_count == 0:
            raise UserError(_('No QC Test Orders were created. They may already exist for these specific lot(s) or lack a lot/batch.'))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('QC Test Orders Created'),
                'message': _('Successfully created %d QC Test Order(s).') % created_count,
                'sticky': False,
                'type': 'success',
                # Reload the queue so has_incoming_qc recomputes and the
                # "Create Test Order" button disappears for these lots.
                'next': {'type': 'ir.actions.client', 'tag': 'reload'},
            }
        }

    def _pharma_move_line_domain(self):
        """Domain for the done stock move lines behind this quant."""
        self.ensure_one()
        if self.lot_id:
            return [('lot_id', '=', self.lot_id.id), ('state', '=', 'done')]
        return [('product_id', '=', self.product_id.id), ('state', '=', 'done')]

    def action_view_stock_moves(self):
        """Open the stock move history for this quant's lot/product."""
        self.ensure_one()
        title = self.lot_id.name or self.product_id.display_name
        return {
            'name': _('Stock Moves — %s', title),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move.line',
            'view_mode': 'list,form',
            'views': [
                (self.env.ref('pharmaceutical_base.view_pharma_move_line_list').id, 'list'),
                (False, 'form'),
            ],
            'search_view_id': (
                self.env.ref('pharmaceutical_base.view_pharma_move_line_search').id, 'search'),
            'domain': self._pharma_move_line_domain(),
            'context': {'create': False},
        }

    def action_quant_open_lot(self):
        """Open the lot / batch record for full details and disposition."""
        self.ensure_one()
        if not self.lot_id:
            raise UserError(_('No lot/batch linked to this record.'))
        return {
            'name': _('Lot / Batch'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.lot',
            'view_mode': 'form',
            'res_id': self.lot_id.id,
            'target': 'current',
        }
