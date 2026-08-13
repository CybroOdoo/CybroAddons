# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jigin K (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License (AGPL) for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    (AGPL) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    """
        This class inherited to add some extra fields in the
        product contains the details of countries
    """
    _inherit = "product.template"

    country_availability = fields.Selection([
        ('all', 'All'),
        ('selected', 'Selected')], string="Available in countries",
        default='all', help='Can select the type all or selected')
    country_selection_ids = fields.One2many('country.details',
                                            'product_tmpl_id',
                                            string='Selected Country',
                                            help='List of countries contains '
                                                 'corresponding products')
