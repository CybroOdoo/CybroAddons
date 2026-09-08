# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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


class ProductTemplate(models.Model):
    """Extends Product Template with waste management categorization and physical properties."""
    _inherit = 'product.template'

    is_waste_material = fields.Boolean(string='Is Waste Material', help='Provides information about is waste material', default=False)
    hazardous = fields.Boolean(string='Hazardous', help='Provides information about hazardous status', default=False)
    recyclable = fields.Boolean(string='Recyclable', help='Provides information about recyclable status', default=True)
    wm_waste_category_id = fields.Many2one('wm.waste.category', string='Waste Category', help='Provides information about waste category')
    compliance_code_id = fields.Many2one('wm.compliance.code', string='Compliance Code', help='Provides information about compliance code')
