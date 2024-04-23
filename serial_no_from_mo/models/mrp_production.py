# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (<https://www.cybrosys.com>)
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
from odoo import models


class MrpProduction(models.Model):
    """Manufacturing Production model for managing production orders.
        This model represents a production order and includes functionality for
         confirming the production, generating serial/lot numbers, and other
          related operations."""
    _inherit = "mrp.production"

    def action_confirm(self):
        """ Confirm the production order and generate serial/lot numbers.
         This method is called when the production order is confirmed.
         It checks the tracking type of the product and the serial_selection
         configuration parameter to determine the generation of serial/lot
         numbers. It generates the numbers based on the global configuration or
          product-specific configuration."""
        parms = self.env['ir.config_parameter'].sudo()
        for rec in self:
            if rec.product_id.tracking in ['serial', 'lot']:
                if parms.get_param(
                        'serial_no_from_mo.serial_selection') == 'global':
                    digit = int(parms.get_param('serial_no_from_mo.digit'))
                    prefix = parms.get_param('serial_no_from_mo.prefix')
                    seq = self.env['ir.sequence'].sudo().search(
                        [('code', '=', 'mrp.production.sequence')])
                    if seq:
                        seq.write({
                            'prefix': prefix,
                            'padding': digit
                        })
                    if not seq:
                        self.env['ir.sequence'].create({
                            'name': 'Mrp Production',
                            'implementation': 'standard',
                            'code': 'mrp.production.sequence',
                            'prefix': prefix,
                            'padding': digit})
                    serial_id = self.env['stock.lot'].create({
                        'name': self.env['ir.sequence'].sudo().next_by_code(
                            'mrp.production.sequence'),
                        'product_id': rec.product_id.id,
                        'company_id': rec.company_id.id,
                    })
                else:
                    seq = self.env['ir.sequence'].sudo().search(
                        [('code', '=', rec.product_id.name)])
                    if seq:
                        seq.write({
                            'prefix': rec.product_id.product_tmpl_id.prefix,
                            'padding': rec.product_id.product_tmpl_id.digit,
                        })
                    if not seq:
                        self.env['ir.sequence'].create({
                            'name': 'Mrp Production',
                            'implementation': 'standard',
                            'code': rec.product_id.name,
                            'prefix': rec.product_id.product_tmpl_id.prefix,
                            'padding': rec.product_id.product_tmpl_id.digit})
                    serial_id = self.env['stock.lot'].create({
                        'name': self.env['ir.sequence'].sudo().next_by_code(
                            rec.product_id.name),
                        'product_id': rec.product_id.id,
                        'company_id': rec.company_id.id,
                    })
                rec.lot_producing_id = serial_id
        return super(MrpProduction, self).action_confirm()
