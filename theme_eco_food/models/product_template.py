# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    """ This model extends the 'product.template' model to add additional
     functionality"""
    _inherit = 'product.template'

    selected_att = fields.Boolean(string='Product Selection',
                                  help='to select multiple category')

    @api.model
    def get_product_selections(self, data):
        """Function to set the value of selected_att based on the selected view
        type in the shop page."""
        for record in self.search([]):
            record.selected_att = data['all']
            if not data['all'] and data['category']:
                for rec in record.public_categ_ids:
                    if rec.id in data['category']:
                        record.selected_att = True
