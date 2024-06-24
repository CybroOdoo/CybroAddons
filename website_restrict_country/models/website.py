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


class Website(models.Model):
    """
        This class inherited to add some extra fields in the
        website backend
    """
    _inherit = 'website'

    country_ids = fields.Many2many(string="Countries",
                                   comodel_name='res.country', required=True,
                                   help='Select a list of countries')
    default_country_id = fields.Many2one(string="Default", required=True,
                                         comodel_name='res.country',
                                         help='Set a default country')
    cart_message = fields.Char(string="Cart Message",
                               help='Custom message display if the product '
                                    'is not available')
