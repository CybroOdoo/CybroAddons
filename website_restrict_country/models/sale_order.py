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
import logging
from functools import reduce
from odoo import models

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    """
        This class inherits to add a function to the sale.order
        for fetching the common country list.
    """
    _inherit = 'sale.order'

    @property
    def get_common_country_list(self):
        """
            This function is added for fetching the common country list.
        """
        lst = []
        for line in self.order_line:
            if line.product_id.product_tmpl_id.country_availability != 'all':
                lst.append(
                    line.product_id.product_tmpl_id.country_selection_ids.mapped(
                        'country_id.id'))
        try:
            country_list = list(
                reduce(lambda i, j: i & j, (set(x) for x in lst)))
        except Exception as error:
            _logger.info(f'Country list has been made empty list due to {error}')
            country_list = []
        return country_list
