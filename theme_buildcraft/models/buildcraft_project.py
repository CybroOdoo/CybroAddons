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

class BuildcraftProject(models.Model):
    _name = 'buildcraft.project'
    _description = 'BuildCraft Project'

    name = fields.Char(string="Project Name", required=True)
    sequence = fields.Integer(string="Sequence", default=10)
    category = fields.Selection([
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('luxury', 'Luxury'),
        ('infrastructure', 'Infrastructure')
    ], string="Category", required=True, default='commercial')
    image = fields.Image(string="Project Image", max_width=1920, max_height=1920)
    location = fields.Char(string="Location", help="e.g. Dubai, UAE")
    value = fields.Char(string="Project Value", help="e.g. AED 380M")
    year = fields.Char(string="Completion Year", help="e.g. 2023")
    description = fields.Html(string="Description", sanitize_style=True)
    client = fields.Char(string="Client Name", help="e.g. Al Futtaim Group")
    area = fields.Char(string="Built-Up Area", help="e.g. 45,000 sq.ft")
    duration = fields.Char(string="Project Duration", help="e.g. 18 Months")
    is_published = fields.Boolean(string="Is Published", default=True)