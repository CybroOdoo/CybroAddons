# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Bhagyadev KP (<https://www.cybrosys.com>)
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
################################################################################
from odoo import fields, models


class PurchaseOrder(models.Model):
    """ This model extends the 'purchase.order' model to include additional
    fields related to document layout, specifically the 'theme_id' field."""
    _inherit = 'purchase.order'

    theme_id = fields.Many2one(
        comodel_name='doc.layout',
        related='company_id.purchase_document_layout_id',
        string='Document Layout Theme',
        help="This field is used to specify the document"
             "layout theme associated with the company's"
             " purchase orders. "
    )
