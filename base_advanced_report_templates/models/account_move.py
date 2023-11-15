# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
################################################################################
from odoo import fields, models


class AccountMove(models.Model):
    """Extends the functionality of the account.move model in Odoo by adding a
     new field.
       """
    _inherit = 'account.move'

    theme_id = fields.Many2one('doc.layout',
                               string="Account Move Template",
                               related='company_id.account_document_layout_id',
                               help='The template to be used for this account '
                                    'move.')


class AccountMoveLine(models.Model):
    """Extends the functionality of the account.move.line model in Odoo by
    adding a new field"""
    _inherit = 'account.move.line'

    order_line_image = fields.Binary(string="Image",
                                     related="product_id.image_128",
                                     help='The image associated with the '
                                          'product of the order line.')
