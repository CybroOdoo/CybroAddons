# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
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
    watermark = fields.Boolean(help="Watermark on report")
    watermark_show = fields.Selection(
        [('logo', 'Company Logo'), ('name', 'Company Name')],
        default='logo', help="Types of Watermark")
