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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from random import randint
from odoo import fields, models


class InvoiceTag(models.Model):
    """Class for creating tags"""
    _name = "invoice.tag"
    _description = "Invoice Tag"

    def _get_default_color(self):
        """Function to select color for tags"""
        return randint(1, 11)

    name = fields.Char(string='Tag Name', required=True, translate=True,
                       help="Invoice tags")
    color = fields.Integer(string='Color', default=_get_default_color,
                           help="Tag color")

    _name_uniq = models.Constraint(
        'unique (name)',
        "Tag name already exists!",
    )


