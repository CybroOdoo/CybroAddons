###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
# pylint: disable=missing-module-docstring,unknown-option-value,too-few-public-methods,no-raise-unlink
from odoo import models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    """Inherit product template to restrict deletion based on user group."""
    _inherit = 'product.template'

    def unlink(self):
        """ Override Odoo unlink method to check if the current user has
           'product_deletion.product_deletion_group_admin' group permissions.

        :raises UserError: If the user lacks the necessary group permissions.
        :returns: Super of the unlink method to proceed with default deletion.
        """
        if not self.env.user.has_group(
            'product_deletion.product_deletion_group_admin',
        ):
            raise UserError(self.env._(
                "You cannot delete the product(s). Please contact the "
                "System Administrator"))
        return super().unlink()
