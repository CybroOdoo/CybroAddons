# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP (Contact : odoo@cybrosys.com)
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
from odoo import models, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    """Inheriting product template for prevent deletion warning"""
    _inherit = 'product.template'

    def unlink(self, default=None):
        """ Override Odoo unlink method to check if the current user has
           'product_deletion.product_deletion_group' group permissions.

        :param default: Unused parameter.
        :raises UserError: If the user lacks the necessary group permissions.
        :returns: Super of the unlink method to proceed with default deletion.
        """
        res_user = self.env['res.users'].search([('id', '=', self._uid)])
        if not res_user.has_group('product_deletion.product_deletion_group'):
            raise UserError(_(
                "You cannot delete the product(s). Please contact the "
                "System Administrator"))
        return super(ProductTemplate, self).unlink()
