# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

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
        displays existing quality alerts generated
        from the given pickings."""
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
        `move_ids` of the given pickings that also have quality measures configured.
        """
        quality_alert = self.env['quality.alert']
        quality_measure = self.env['quality.measure']
        for picking in self:
            for move in picking.move_ids:
                measures = quality_measure.search([
                    ('product_id', '=', move.product_id.id),
                    ('picking_type_ids', 'in', picking.picking_type_id.id)
                ])
                if measures:
                    quality_alert.create({
                        'product_id': move.product_id.id,
                        'picking_id': picking.id,
                        'origin': picking.name,
                        'company_id': picking.company_id.id,
                    })

    def action_confirm(self):
        """If `alert_count` is zero, it triggers the `generate_quality_alert` method
        before proceeding with the standard `action_confirm` behavior."""
        self.filtered(lambda p: p.alert_count == 0).generate_quality_alert()
        return super(StockPicking, self).action_confirm()


    def _action_done(self):
        """Check for pending or failed quality alerts before validating the picking."""
        for picking in self:
            alerts = self.env['quality.alert'].search([('picking_id', '=', picking.id)])
            for alert in alerts:
                if alert.final_status == 'wait':
                    raise UserError(_('There are items still in quality test'))
                if alert.final_status == 'fail':
                    raise UserError(_('There are items failed in quality test'))
        return super(StockPicking, self)._action_done()
