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


class ResCompany(models.Model):
    """Model is inherited to add the
    base_layout_purchase selection field"""
    _inherit = 'res.company'

    base_layout_purchase = fields.Selection(
        selection=[('normal', 'Normal'), ('modern', 'Modern'),
                   ('old', 'Old Standard'), ('default', 'Default')],
        string="Purchase Order Document Layout", default="default",
        help='Select the Layout of the Purchase Order Document')
    document_layout_purchase_id = fields.Many2one(
        "doc.layout.purchase",
        string="Purchase Order Layout Configuration",
        help='Configuration of Purchase Order Layout')
