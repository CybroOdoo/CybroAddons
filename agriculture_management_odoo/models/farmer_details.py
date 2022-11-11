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
from odoo import models, fields, api


class FarmerDetails(models.Model):
    _name = 'farmer.details'
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _description = 'Farmer Details'
    _rec_name = 'farmer_name'

    farmer_name = fields.Many2one('res.partner', string='Farmer', required=True,
                                  tracking=True)
    farmer_image = fields.Binary(string='Image', tracking=True)
    note = fields.Text(string='Notes', tracking=True)

    @api.onchange('farmer_name')
    def onchange_farmer_name(self):
        if self.farmer_name:
            self.farmer_image = self.farmer_name.image_1920
