# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Amaya Aravind (odoo@cybrosys.com)
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
from odoo import api, models


class ProductPricelist(models.Model):
    """Class for the inherited model product_pricelist. Checking and filtering
        the applied pricelists for the uses by supering the _search() method.
    """
    _inherit = 'product.pricelist'

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False,
                access_rights_uid=None):
        """Checking and filtering the applied pricelists for the uses by
           supering the _search() method """
        pricelist_restricted = self.env[
            'ir.config_parameter'].sudo().get_param(
            'restrict_pricelist_user.is_restricted')
        if pricelist_restricted and self.env.user.pricelist_ids.ids:
            args.append(('id', 'in', self.env.user.pricelist_ids.ids))
        return super(ProductPricelist, self)\
            ._search(args, offset, limit, order, count=count,
                     access_rights_uid=access_rights_uid)
