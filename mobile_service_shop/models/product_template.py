# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu KP S (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    """Inherits the model product.template to extend and add fields"""
    _inherit = 'product.template'

    is_a_parts = fields.Boolean(
        'Is a Mobile Part', default=False,
        help="Specify if the product is a mobile part or not.")
    brand_name = fields.Many2one('mobile.brand', string="Brand",
                                 help="Select a mobile brand for the part.")
    model_name = fields.Many2one('brand.model', string="Model Name",
                                 domain="[('mobile_brand_name','=',brand_name)]",
                                 help="Select a model for the part.")
    model_colour = fields.Char(string="Colour", help="Colour for the part.")
    extra_descriptions = fields.Text(string="Note", help="Extra description "
                                                         "for the part.")
