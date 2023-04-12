# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    pd = fields.Boolean(string='Product Selection')

    @api.model
    def get_product_selections(self, arr):
        records = self.env['product.template'].browse(arr['product_ids'])
        if arr['checked'] == 0:
            for rec in records:
                rec.pd = True
        elif arr['checked'] == 1:
            for rec in records:
                rec.pd = False
        elif arr['checked'] == -1:
            for rec in self.env['product.template'].search([]):
                rec.pd = True

