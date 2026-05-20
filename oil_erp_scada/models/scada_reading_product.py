# -*- coding: utf-8 -*-
#############################################################################
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import fields, models

class ScadaReadingProduct(models.Model):
    _name = 'scada.reading.product'
    _description = 'SCADA Reading Product Quantity'

    reading_id = fields.Many2one(
        'scada.reading',
        string='Reading',
        required=True,
        ondelete='cascade',
        index=True
    )
    timestamp = fields.Datetime(
        string='Timestamp',
        related='reading_id.timestamp',
        store=True,
        index=True
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        index=True
    )
    tag_id = fields.Many2one(
        'scada.tag',
        related='reading_id.tag_id',
        store=True,
        string='SCADA Tag',
        index=True
    )
    produced_qty = fields.Float(
        string='Produced Quantity',
        required=True,
        digits=(16, 4)
    )
