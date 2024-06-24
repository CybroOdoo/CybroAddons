# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ammu Raj (odoo@cybrosys.com)
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
    select_country_id = fields.Many2one(string='Select Country Id',
                                        comodel_name='product.template',
                                        help='User can select the country id')
