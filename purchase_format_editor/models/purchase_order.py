# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Abhin K(odoo@cybrosys.com)
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
from odoo import fields, models


class PurchaseOrder(models.Model):
    """Model is inherited to add
    theme_id_purchase and base_layout_purchase fields"""
    _inherit = 'purchase.order'

    base_layout_purchase = fields.Selection(
        selection=[('normal', 'Normal'), ('modern', 'Modern'),
                   ('old', 'Old Standard'), ('default', 'Default')],
        string='Base Layout Purchase', help='Select Base Layout of Purchase')
    theme_id_purchase = fields.Many2one(
        comodel_name='doc.layout.purchase', string="Theme Id Purchase",
        related='company_id.document_layout_purchase_id',
        help='The theme ID for the purchase document layout. It is related '
             'to the document layout ID of the company. This field helps in '
             'selecting the specific theme for the purchase documents.')
