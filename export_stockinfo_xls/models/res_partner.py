# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:Cybrosys Techno Solutions(odoo@cybrosys.com)
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
#############################################################################

from odoo import models, fields


class Partner(models.Model):
    _inherit = 'res.partner'

    supplier_id = fields.Many2many('wizard.stock.history', 'supp_wiz_rel', 'wiz', 'supp', invisible=True)


class Category(models.Model):
    _inherit = 'product.category'

    obj = fields.Many2many('wizard.stock.history', 'categ_wiz_rel', 'wiz', 'categ', invisible=True)


class Warehouse(models.Model):
    _inherit = 'stock.warehouse'

    obj = fields.Many2many('wizard.stock.history',  'wh_wiz_rel', 'wiz', 'wh', invisible=True)
