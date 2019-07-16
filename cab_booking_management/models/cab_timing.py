# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2008-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nilmar Shereef(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api


class CabTiming(models.Model):
    _name = 'cab.timing'

    name = fields.Many2one('cab.management', string="Cab Name", required=True)
    cab_time = fields.Many2many('cab.time', 'cab_name_rel', string="Time", required=True,
                                help="Use this format 00:00,ex:  01:15")
    cab_route = fields.Many2one('cab.location', string='Starting Place', required=True)
    cab_route_to = fields.Many2one('cab.location', string='Destination Place', required=True)
    seat = fields.Integer(string="Seating Capacity", related='name.seating_capacity', required=True)

    @api.multi
    def action_log_form_view(self):
        return {
            'name': 'CabLog',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'cab.log',
            'type': 'ir.actions.act_window',
            'target': 'current'
        }


class Time(models.Model):
    _name = 'cab.time'

    name = fields.Char(string="Name", required=True, help="Use this format 00:00,ex:  01:15")





