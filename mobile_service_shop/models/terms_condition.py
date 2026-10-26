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
from odoo import fields, models


class TermsConditions(models.Model):
    """Used to add the Mobile Service Terms and Conditions"""
    _name = 'terms.conditions'
    _description = 'Terms and Conditions'
    _rec_name = 'terms_id'

    terms_id = fields.Char(string="Terms and condition",
                           compute="_compute_terms_id",
                           help="Identifier of the terms and conditions.")
    terms_conditions = fields.Text(string="Terms and Conditions",
                                   help="Details of terms and conditions.")

    def _compute_terms_id(self):
        """Return the terms ID"""
        for record in self:
            record.terms_id = str(record.id) if record.id else ''
