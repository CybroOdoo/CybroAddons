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


class CountryDetails(models.Model):
    """
        Added a new model and added some fields with the details of the
        countries
    """
    _name = "country.details"
    _description = 'Country Details'

    country_id = fields.Many2one(string="Country", comodel_name='res.country',
                                 help='User can select the country',
                                 required=True)
    country_code = fields.Char(related='country_id.code', string="Country Code",
                               help='The code of the corresponding country')
    product_tmpl_id = fields.Many2one(string='Product',
                                      comodel_name='product.template',
                                      help='Product for which this country '
                                           'availability is configured')
