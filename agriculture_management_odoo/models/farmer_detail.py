# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vyshnav AR(<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class FarmerDetail(models.Model):
    """This model represents comprehensive details about farmers within the
    context of agriculture management. It provides a structured way to store
    information related to individual farmers, including their personal and
    contact details. """
    _name = 'farmer.detail'
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _description = 'Farmer Details In Agriculture Management'
    _rec_name = 'farmer_id'

    farmer_id = fields.Many2one('res.partner', string='Farmer',
                                help=' Select the corresponding farmer',
                                required=True, tracking=True)
    farmer_image = fields.Binary(string='Image', copy=False,
                                 help='Upload image of Farmer')
    note = fields.Text(string='Notes', tracking=True,
                       help="Description regarding the farmer")
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        readonly=True, help='The company associated with the current user or '
                            'environment.',
        default=lambda self: self.env.company)

    @api.onchange('farmer_id')
    def _onchange_farmer_id(self):
        """Function for select image of farmer automatically when choosing
        the farmer"""
        for record in self:
            if record.farmer_id:
                record.farmer_image = record.farmer_id.image_1920
