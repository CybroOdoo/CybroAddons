# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models, fields


class DamageLossDetails(models.Model):
    _name = 'damage.loss'
    _inherit = ["mail.thread", 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, tracking=True)
    farmer_id = fields.Many2one('farmer.details', string='Farmer',
                                required=True, tracking=True)
    crop_id = fields.Many2one('crop.requests', string='Crop', required=True,
                              tracking=True)
    location_id = fields.Many2one('location.details', string='Location',
                                  required=True, tracking=True)
    damage_loss_type = fields.Selection(
        [('damage', 'Damage'), ('loss', 'Loss')], string='Damage/Loss Type',
        required=True, tracking=True)
    damage_loss_date = fields.Date(string='Damage/Loss Date',
                                   default=fields.Date.context_today,
                                   required=True, tracking=True)
    note = fields.Text(string='Damage/Loss Description', tracking=True)
    damage_loss_image = fields.Binary(string='Image', tracking=True)
