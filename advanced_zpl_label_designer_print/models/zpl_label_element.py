# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import api,fields,models

class ZplLabelElement(models.Model):
    """A single positioned design element (text, barcode, QR code, image,
    line or rectangle) belonging to a ZPL label template."""
    _name = 'zpl.label.element'
    _description = 'ZPL Label Element'
    _order = 'sequence'

    template_id = fields.Many2one('zpl.label.template', string='Template', ondelete='cascade', required=True,help='template')
    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Name', required=True)
    type = fields.Selection([
        ('text', 'Text'),
        ('barcode', 'Barcode'),
        ('qrcode', 'QR Code'),
        ('image', 'Image'),
        ('line', 'Line'),
        ('rect', 'Rectangle')
    ], string='Type', default='text', required=True)
    
    x_pos = fields.Integer(string='X Position', default=0)
    y_pos = fields.Integer(string='Y Position', default=0)
    width = fields.Integer(string='Width', default=100)
    height = fields.Integer(string='Height', default=50)
    thickness = fields.Integer(string='Thickness', default=2)
    rounding = fields.Integer(string='Rounding', default=0)
    
    font_size = fields.Integer(string='Font Size', default=20)
    rotation = fields.Selection([
        ('0', '0°'),
        ('90', '90°'),
        ('180', '180°'),
        ('270', '270°')
    ], string='Rotation', default='0')
    
    model_id = fields.Many2one('ir.model', related='template_id.model_id', string='Model', readonly=True)
    field_id = fields.Many2one('ir.model.fields', string='Odoo Field', ondelete='cascade', domain="[('model_id', '=', model_id)]", help="The Odoo field to pull data from (e.g., default_code for barcode)")
    data_format = fields.Char(string='Data Format', help="A string placeholder like Price: {{price}}")
    
    barcode_type = fields.Selection([
        ('code128', 'Code 128'),
        ('code39', 'Code 39'),
        ('ean13', 'EAN 13'),
        ('upca', 'UPC-A')
    ], string='Barcode Type')
    
    active = fields.Boolean(default=True)
