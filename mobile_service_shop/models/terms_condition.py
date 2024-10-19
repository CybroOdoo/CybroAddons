# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Jumana Jabin MP (odoo@cybrosys.com)
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
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class TermsConditions(models.Model):
    """Used to add the Mobile Service Terms and Conditions"""
    _name = 'terms.conditions'
    _description = 'Terms and Conditions'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'terms_id'

    terms_id = fields.Char(String="Terms and condition",
                           compute="_compute_terms_id", help="this will be "
                                                             "the terms id.")
    terms_conditions = fields.Text(string="Terms and Conditions",
                                   help="this will be the terms and "
                                        "conditions space.")

    def _compute_terms_id(self):
        """Return the terms ID"""
        self.terms_id = self.id or ''
