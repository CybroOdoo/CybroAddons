# -*- coding: utf-8 -*-
################################################################################
#
#   Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#   Author: Mohammed Ajmal P (odoo@cybrosys.com)
#
#   You can modify it under the terms of the GNU AFFERO
#   GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#   This program is distributes in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#   You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#   (AGPL v3) along this program.
#   If not, see <http://www.gnu.org/license/>.
#
################################################################################

from odoo import fields, models


class SaleOrder(models.Model):
    """Field to identify the type of Order in to Sale Purchase Report"""
    _inherit = 'sale.order'

    is_sale_order = fields.Boolean(default=True)
