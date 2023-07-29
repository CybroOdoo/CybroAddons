# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Prathyunnan R (odoo@cybrosys.com)
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
#############################################################################
from odoo import fields, models


class CustomerGroup(models.Model):
    """New model to create customer group price list."""
    _name = 'customer.group'
    _description = 'Create Customer Groups'

    name = fields.Char(string='Name', help='Name of the Pricelist')
    contact_ids = fields.Many2many('res.partner', string='Contacts',
                                   help='Add contacts to the customer group')
    pricelist_id = fields.Many2one('product.pricelist', string='PriceList',
                                   help='Add Pricelist for apply on the '
                                        'customer group')
