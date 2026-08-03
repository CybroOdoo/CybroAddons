# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
################################################################################
from odoo import models, fields

class GreenscapeProject(models.Model):
    _name = 'greenscape.project'
    _description = 'Greenscape Project'
    _order = 'year desc, id desc'

    name = fields.Char(
        string='Project Name',
        required=True,
        help = 'Enter the display name of the landscaping project.'
    )
    description = fields.Text(
        string='Description',
        help='Add a short summary of the project scope, work completed, or result.'
    )
    category = fields.Selection(
        [
            ('residential', 'Residential'),
            ('commercial', 'Commercial'),
            ('garden', 'Garden Design'),
            ('hardscaping', 'Hardscaping'),
            ('lawn', 'Lawn Care')
        ],
        string='Category',
        required=True,
        help='Choose the service category used to filter this project on the website.'
    )
    image = fields.Image(
        string='Project Image',
        required=True,
        help='Upload the image shown for this project in the website portfolio.'
    )
    location = fields.Char(
        string='Location',
        help="Enter the project location, for example: Bel Air, CA."
    )
    year = fields.Char(
        string='Year Completed',
        help='Enter the year the project was completed, for example: 2024.'
    )
    is_published = fields.Boolean(
        string='Published on Website',
        default=True,
        help='Enable this option to show the project on the public projects page.'
    )
