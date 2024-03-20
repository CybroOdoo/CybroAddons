# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swathy K S (odoo@cybrosys.com)
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
##############################################################################
from odoo import models, fields


class ResCompany(models.Model):
    """Inheriting the res company model for adding sale document
        layout details"""
    _inherit = 'res.company'

    base_layout = fields.Selection(
        [('default', 'Default'), ('modern', 'Modern'),
         ('normal', 'Normal'), ('old', 'Old Standard'),
         ], string="Sale Document Layout", default="default",
        help="Sale document base layout types")
    document_layout_id = fields.Many2one("doc.layout",
                                         string="Sale Layout Configuration",
                                         help="Configuration of sale "
                                              "document layout")
    watermark = fields.Boolean(string='Watermark', help="Watermark on report")
    watermark_show = fields.Selection(
        [('logo', 'Company Logo'), ('name', 'Company Name')],
        default='logo', string="Watermark Show", help="Types of Watermark")
