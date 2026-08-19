# -- coding: utf-8 --
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
from odoo import fields, models

class ProductDesignTemplateTag(models.Model):
    """Model representing tags used to categorize design templates."""
    _name = 'product.design.template.tag'
    _description = 'Design Template Tag'
    _order = 'name'

    name = fields.Char(
        string="Tag Name",
        required=True,
        translate=True,
        help="Label for categorizing templates. Examples: 'Professional', 'Colorful', "
             "'Photo-based', 'Seasonal', 'Holiday', 'Wedding'."
    )
    color = fields.Integer(
        string="Color Index",
        default=0,
        help="Color index for the tag badge in list/kanban views (0-11). "
             "Each number maps to a different color in Odoo's color palette."
    )
