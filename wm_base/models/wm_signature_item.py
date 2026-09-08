# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class WmSignatureItem(models.Model):
    """Template layout element representing a signature, name, date, or text field on a PDF."""
    _name = 'wm.signature.item'
    _description = 'Signature Item'

    template_id = fields.Many2one('wm.signature.template', string='Template', required=True, ondelete='cascade')
    page = fields.Integer(string='Page Number', required=True, default=1)
    x = fields.Float(string='X Position (%)', required=True)
    y = fields.Float(string='Y Position (%)', required=True)
    width = fields.Float(string='Width (%)', required=True)
    height = fields.Float(string='Height (%)', required=True)
    type = fields.Selection([
        ('signature', 'Signature'),
        ('name', 'Name'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('company', 'Company'),
        ('text', 'Text'),
        ('date', 'Date'),
    ], string='Type', required=True, default='signature')
    role_id = fields.Many2one('wm.signature.role', string='Responsible Role', required=True)


class WmSignatureRequestItemValue(models.Model):
    """Captured value and coordinates for a signature item filled during a signing session."""
    _name = 'wm.signature.request.item.value'
    _description = 'Signature Request Item Value'

    request_id = fields.Many2one('wm.signature.request', string='Signature Request', required=True, ondelete='cascade')
    item_id = fields.Many2one('wm.signature.item', string='Template Item', required=True, ondelete='cascade')
    value = fields.Text(string='Value')
    signature_image = fields.Binary(string='Signature Image', attachment=True)
    signer_id = fields.Many2one('wm.signature.request.signer', string='Signer', required=True, ondelete='cascade')
