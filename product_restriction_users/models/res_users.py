# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Jabin MP (odoo@cybrosys.com)
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


class ResUsers(models.Model):
    """ Inherited the res_users model for adding the products
    and product category"""
    _inherit = 'res.users'

    restricted_type = fields.Selection([('product', 'Product'), (
        'category', 'Category')], string='Restriction Type', default='product',
                                       help='choose Product and Product '
                                            'category depends upon your need')
    allowed_product_ids = fields.Many2many('product.template',
                                           string="Products", store=True,
                                           help='Show to allow the products '
                                                'for assigned users')
    allowed_product_category_ids = fields.Many2many('product.category',
                                                    string="Product Category",
                                                    store=True,
                                                    help='Show to allow the '
                                                         'product category for'
                                                         'assigned users')
    is_admin = fields.Boolean(compute='_compute_is_admin',
                              help='Check the user is admin or not',
                              string="Admin")

    def write(self, vals):
        """Write the values of restrict user ids """
        res = super(ResUsers, self).write(vals)
        if self.restricted_type == 'product':
            products = self.env['product.template'].sudo(). \
                search([('restrict_user_ids', 'in', self.ids)])
            if self.allowed_product_ids:
                for product in products:
                    product.is_product = True
                for product in self.env['product.template'].sudo(). \
                        search([('restrict_user_ids', 'not in',
                                 [rec.id for rec in products])]):
                    product.is_product = False
            else:
                for product in self.env['product.template'].sudo().search([]):
                    product.is_product = True
            for user_product in self.allowed_product_ids:
                user_product.sudo().write({
                    'restrict_user_ids': [(4, user.id) for user in self]
                })
        else:
            if self.allowed_product_category_ids:
                products = self.env['product.template'].sudo().search([])
                products.restrict_user_ids = [(3, user.id) for user in self]
                products.is_product = False
                products_categ = self.env['product.template']. \
                    search([('categ_id', 'in', [int(categ.id) for categ in
                                                self.allowed_product_category_ids])
                            ])
                for product in products_categ:
                    product.is_product = False
                    product.sudo().write({
                        'restrict_user_ids': [(4, user.id) for user in self]
                    })
            else:
                products = self.env['product.template'].sudo().search([])
                products.is_product = True
        return res

    def _compute_is_admin(self):
        """ Compute the value of is_admin based on the user id admin or not"""
        for admin in self:
            admin.is_admin = False
            if admin.id == self.env.ref('base.user_admin').id:
                admin.is_admin = True
