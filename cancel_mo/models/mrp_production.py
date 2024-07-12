# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Saneen K (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from collections import defaultdict
from odoo import fields, models


class MrpProduction(models.Model):
    """inheriting 'mrp.production' to add more functionality"""
    _inherit = 'mrp.production'

    is_cancel_mo_active = fields.Boolean(string="Cancel Button",
                                         help='The field that compute whether '
                                              'enable the cancel mo in res'
                                              ' config settings',
                                         compute='_compute_is_cancel_mo_active')

    def _compute_is_cancel_mo_active(self):
        """Compute the value of the 'is_cancel_mo_active' field
        based on the current state and specific configuration
        parameters."""
        inventory_move = self.env['ir.config_parameter'].sudo().get_param(
            'cancel_mo.is_cancel_inventory_moves')
        work_order = self.env['ir.config_parameter'].sudo().get_param(
            'cancel_mo.is_cancel_workorder')
        if self.state == 'done' and (inventory_move or work_order):
            self.is_cancel_mo_active = True
        else:
            self.is_cancel_mo_active = False

    def action_cancel_mo(self):
        """Cancels the mo"""
        inventory_move_status = self.env[
            'ir.config_parameter'].sudo().get_param(
            'cancel_mo.is_cancel_inventory_moves')
        work_order_status = self.env['ir.config_parameter'].sudo().get_param(
            'cancel_mo.is_cancel_workorder')
        if inventory_move_status:
            self.state = 'cancel'
            move_lines_ids = self.env['stock.move.line'].search(
                [('reference', '=', self.name)])
            for rec in move_lines_ids:
                rec.write({'state': 'cancel'})
        if work_order_status:
            work_order_ids = self.env['mrp.workorder'].search(
                [('production_id', '=', self.id)])
            for rec in work_order_ids:
                rec.action_cancel()

    def _action_cancel(self):
        """Overriding the cancel methode"""
        documents_by_production = {}
        for production in self:
            documents = defaultdict(list)
            for move_raw_id in self.move_raw_ids.filtered(
                    lambda m: m.state not in ('done', 'cancel')):
                iterate_key = self._get_document_iterate_key(move_raw_id)
                if iterate_key:
                    document = self.env['stock.picking']._log_activity_get_documents(
                        {move_raw_id: (move_raw_id.product_uom_qty, 0)},
                        iterate_key, 'UP')
                    for key, value in document.items():
                        documents[key] += [value]
            if documents:
                documents_by_production[production] = documents
            # log an activity on Parent MO if child MO is cancelled.
            finish_moves = production.move_finished_ids.filtered(
                lambda x: x.state not in ('done', 'cancel'))
            if finish_moves:
                production._log_downside_manufactured_quantity(
                    {finish_move: (production.product_uom_qty, 0.0) for
                     finish_move in finish_moves}, cancel=True)

        self.workorder_ids.filtered(
            lambda x: x.state not in ['cancel']).action_cancel()
        finish_moves = self.move_finished_ids.filtered(
            lambda x: x.state not in ('done', 'cancel'))
        raw_moves = self.move_raw_ids.filtered(
            lambda x: x.state not in ('done', 'cancel'))
        (finish_moves | raw_moves)._action_cancel()
        picking_ids = self.picking_ids.filtered(
            lambda x: x.state not in ('cancel'))
        picking_ids.action_cancel()

        for production, documents in documents_by_production.items():
            filtered_documents = {}
            for (parent, responsible), rendering_context in documents.items():
                if not parent or parent._name == 'stock.picking' and parent.state == 'cancel' or parent == production:
                    continue
                filtered_documents[(parent, responsible)] = rendering_context
            production._log_manufacture_exception(filtered_documents,
                                                  cancel=True)
        # In case of a flexible BOM, we don't know from the state of the moves if the MO should
        # remain in progress or done. Indeed, if all moves are done/cancel but the quantity produced
        # is lower than expected, it might mean:
        # - we have used all components but we still want to produce the quantity expected
        # - we have used all components and we won't be able to produce the last units
        #
        # However, if the user clicks on 'Cancel', it is expected that the MO is either done or
        # canceled. If the MO is still in progress at this point, it means that the move raws
        # are either all done or a mix of done / canceled => the MO should be done.
        self.filtered(lambda p: p.state not in ['done', 'cancel'] and
                                p.bom_id.consumption == 'flexible').write(
            {'state': 'done'})
        return True
