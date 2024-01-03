# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Dhanya Babu (odoo@cybrosys.com)
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
##############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inherited the model to add the 'sale_purchase_sync' fields"""
    _inherit = 'res.config.settings'

    sale_purchase_sync = fields.Boolean(string='Synchronization',
                                        config_parameter='inter_company_synchronization.sale_purchase_sync',
                                        help='Boolean field is use to enable '
                                             'the inter company sale and '
                                             'purchase synchronization')
