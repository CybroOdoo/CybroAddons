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
from odoo import fields, models


class DamageLoss(models.Model):
    """This model represents details about damage and loss incidents.
    It provides a structured way to record information related to damages and
    losses incurred in the context of agricultural activities or other domains.
    """
    _name = 'damage.loss'
    _description = 'Damage Loss Details'
    _inherit = ["mail.thread", 'mail.activity.mixin']

    name = fields.Char(string='Name', help="Reason for damage or loss of crop ",
                       required=True, tracking=True)
    farmer_id = fields.Many2one('farmer.detail',
                                help=" Mention the corresponding Farmer",
                                string='Farmer', required=True, tracking=True)
    crop_id = fields.Many2one('crop.request',
                              help="Mention the corresponding crop",
                              string='Crop', required=True, tracking=True)
    location_id = fields.Many2one('location.detail', tracking=True,
                                  string='Location', help="The location of the "
                                  "damage or loss takes place",
                                  required=True)
    damage_loss_type = fields.Selection([('damage', 'Damage'),
                                        ('loss', 'Loss')],
                                        string='Damage/Loss Type',
                                        help="Mention the damage or lass type",
                                        required=True, tracking=True)
    damage_loss_date = fields.Date(string='Damage/Loss Date',
                                   help="The date in which damage occurs",
                                   default=fields.Date.context_today,
                                   required=True, tracking=True)
    note = fields.Text(string='Damage/Loss Description', tracking=True,
                       help="Describe the details of damage/loss")
    damage_loss_image = fields.Binary(string='Image', tracking=True,
                                      help="Upload some images of damage/loss")
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        readonly=True,help='The company associated with the current user or '
        'environment.', default=lambda self: self.env.company)
