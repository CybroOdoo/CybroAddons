# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Dhanya B(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.depends('move_ids')
    def _compute_quality_alert(self):
        '''
        This function computes the number of
        quality alerts generated from given picking.
        '''
        for picking in self:
            alerts = self.env['quality.alert'].search(
                [('picking_id', '=', picking.id)])
            picking.alert_ids = alerts
            picking.alert_count = len(alerts)

    def action_quality_alert(self):
        """This function returns an action that
        display existing quality alerts generated
        from a given picking."""
        action = self.env.ref('quality_assurance.quality_alert_action')
        result = action.read()[0]
        # override the context to get rid of the default filtering on picking type
        result.pop('id', None)
        result['context'] = {}
        alert_ids = sum([picking.alert_ids.ids for picking in self], [])
        if len(alert_ids) > 1:
            result['domain'] = "[('id','in',[" + ','.join(
                map(str, alert_ids)) + "])]"
        elif len(alert_ids) == 1:
            res = self.env.ref('quality_assurance.quality_alert_view_form',
                               False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = alert_ids and alert_ids[0] or False
        return result

    alert_count = fields.Integer(compute='_compute_quality_alert',
                                 string='Quality Alerts', default=0)
    alert_ids = fields.Many2many('quality.alert',
                                 compute='_compute_quality_alert',
                                 string='Quality Alerts', copy=False)

    def generate_quality_alert(self):
        """
        This function generates quality alerts for the products mentioned in
        `move_ids` of the given picking and also have quality measures configured.
        """
        quality_alert = self.env['quality.alert']
        quality_measure = self.env['quality.measure']
        for move in self.move_ids:
            measures = quality_measure.search([
                ('product_id', '=', move.product_id.id),
                ('picking_type_ids', 'in', self.picking_type_id.id)
            ])
            if measures:
                quality_alert.create({
                    'name': self.env['ir.sequence'].next_by_code(
                        'quality.alert') or _('New'),
                    'product_id': move.product_id.id,
                    'picking_id': self.id,
                    'origin': self.name,
                    'company_id': self.company_id.id,
                })

    def action_confirm(self):
        """If `alert_count` is zero, it triggers the `generate_quality_alert` method
        before proceeding with the standard `action_confirm` behavior."""
        if self.alert_count == 0:
            self.generate_quality_alert()
        return super(StockPicking, self).action_confirm()

    def force_assign(self):
        """Forces the assignment of stock picking.
        If `alert_count` is zero, it triggers the `generate_quality_alert` method
        before proceeding with the standard `force_assign` behavior.
        """
        if self.alert_count == 0:
            self.generate_quality_alert()
        return super(StockPicking, self).force_assign()

    def _action_done(self):
        """Changes picking state to done by processing the Stock Moves of
        the Picking
        Normally that happens when the button "Done" is pressed on a
        Picking view.
        @return: True
        """
        todo_moves = self.mapped('move_ids').filtered(
            lambda self: self.state in ['draft', 'partially_available',
                                        'assigned', 'confirmed'])
        # Check if there are ops not linked to moves yet
        for pick in self:
            for ops in pick.move_line_ids.filtered(lambda x: not x.move_id):
                # Search move with this product
                moves = pick.move_ids.filtered(
                    lambda x: x.product_id == ops.product_id)
                if moves:
                    ops.move_id = moves[0].id
                else:
                    new_move = self.env['stock.move'].create({
                        'name': _('New Move:') + ops.product_id.display_name,
                        'product_id': ops.product_id.id,
                        'product_uom_qty': ops.qty_done,
                        'product_uom': ops.product_uom_id.id,
                        'location_id': pick.location_id.id,
                        'location_dest_id': pick.location_dest_id.id,
                        'picking_id': pick.id,
                    })
                    ops.move_id = new_move.id
                    new_move._action_confirm()
                    todo_moves |= new_move
        for move in todo_moves:
            alerts = self.env['quality.alert'].search(
                [('picking_id', '=', self.id),
                 ('product_id', '=', move.product_id.id)])
            for alert in alerts:
                if alert.final_status == 'wait':
                    raise UserError(_('There are items still in quality test'))
                if alert.final_status == 'fail':
                    raise UserError(_('There are items failed in quality test'))
        todo_moves._action_done()
        self.write({'date_done': fields.Datetime.now()})
        return True
