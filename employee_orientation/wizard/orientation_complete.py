# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anusha @cybrosys(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, fields, models, _


class OrientationForceComplete(models.TransientModel):
    _name = 'orientation.force.complete'

    name = fields.Char()
    orientation_id = fields.Many2one('employee.orientation', string='Orientation')
    orientation_lines = fields.One2many('orientation.request', string='Orientation Lines', compute='pending_lines')

    @api.onchange('orientation_id')
    def pending_lines(self):
        pending = []

        for data in self.orientation_id.orientation_request:
            if data.state == 'new':
                pending.append(data.id)
        self.update({'orientation_lines': pending})

    def force_complete(self):
        for line in self.orientation_lines:
            if line.state != 'cancel':
                line.state = 'complete'
        self.orientation_id.write({'state': 'complete'})



