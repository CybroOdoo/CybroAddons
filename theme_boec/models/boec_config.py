# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
from odoo import fields, models


class BoecConfig(models.Model):
    """Allows to set a product that will deal of the week. It is a snippet"""
    _name = 'boec.config'
    _description = 'Boec Config'

    name = fields.Char(string='Name', help='Name of the Deal')
    deal_week_product_id = fields.Many2one('product.product',
                                           domain=[('is_published', '=', True)],
                                           string='Deal of the Week Product',
                                           help='This product will be the deal'
                                                'of the week')
    date_end = fields.Datetime(string='Counter End Date', help='End date of'
                                                               'this offer')
