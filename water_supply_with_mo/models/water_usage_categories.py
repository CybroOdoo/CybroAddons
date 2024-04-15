# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (odoo@cybrosys.com)
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
##############################################################################
from odoo import fields, models


class WaterUsageCategories(models.Model):
    """Creating water usage categories."""
    _name = 'water.usage.categories'
    _description = 'Water Usage Categories'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'usage_category_name'

    code = fields.Char(string='Usage Category Code',
                       help='Usage category code')
    usage_category_name = fields.Char(string='Usage Category Name',
                                      help='Usage category name')
