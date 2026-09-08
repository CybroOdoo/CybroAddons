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
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class WmRouteLine(models.Model):
    """Ordered collection stop line within a route, linking collection points and execution status."""
    _name = 'wm.route.line'
    _description = 'Route Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    route_id = fields.Many2one('wm.route', string='Route')
    sequence = fields.Integer(string='Sequence', default=10)
    collection_point_id = fields.Many2one('wm.collection.point', string='Collection Point')

    @api.model_create_multi
    def create(self, vals_list):
        """
        Prevent adding stops to a route if the route is already in completed state.
        """
        for vals in vals_list:
            if vals.get('route_id') and not self.env.su and not self.env.context.get('programmatic_state_change'):
                route = self.env['wm.route'].browse(vals['route_id'])
                if route.state == 'completed':
                    raise UserError(_(
                        "Cannot add stops to route '%(name)s' because it is already completed.",
                        name=route.name,
                    ))
        return super().create(vals_list)

    def write(self, vals):
        """
        Prevent modifying stops on a route if the route is already in completed state.
        """
        if not self.env.su and not self.env.context.get('programmatic_state_change'):
            for line in self:
                if line.route_id and line.route_id.state == 'completed':
                    raise UserError(_(
                        "Cannot modify stop on route '%(name)s' because it is already completed.",
                        name=line.route_id.name,
                    ))
        return super().write(vals)

    def unlink(self):
        """
        Prevent deleting stops from a route if the route is already in completed state.
        """
        if not self.env.su and not self.env.context.get('programmatic_state_change'):
            for line in self:
                if line.route_id and line.route_id.state == 'completed':
                    raise UserError(_(
                        "Cannot delete stop from route '%(name)s' because it is already completed.",
                        name=line.route_id.name,
                    ))
        return super().unlink()
