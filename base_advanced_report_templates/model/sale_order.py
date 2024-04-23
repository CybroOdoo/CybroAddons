# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import models, fields


class SaleOrder(models.Model):
    """ This model extends the 'sale.order' model to include additional fields
    related to customer images and document layout themes."""
    _inherit = 'sale.order'

    customer_image = fields.Binary(string="Image",
                                   related="partner_id.image_1920",
                                   help="This field represents the image "
                                        "associated with the customer on the"
                                        " sale order.")

    theme_id = fields.Many2one('doc.layout',
                               related='company_id.sale_document_layout_id',
                               string='Document Layout Theme',
                               help="This field is used to specify the document"
                                    "layout theme associated with the company's"
                                    "sale orders."
                               )
