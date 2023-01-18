# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    digit = fields.Integer(string="Number of Digits")
    prefix = fields.Char(string="Prefix")


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def action_confirm(self):
        parms = self.env['ir.config_parameter'].sudo()
        type = parms.get_param('serial_selection')
        for rec in self:
            if rec.product_id.tracking == 'serial' or rec.product_id.tracking == 'lot':
                if type == 'global':
                    digit = parms.get_param('digit')
                    prefix = parms.get_param('prefix')
                    seq = self.env['ir.sequence'].sudo().search([('code', '=', 'mrp.production.sequence')])

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
                    serial_id = self.env['stock.production.lot'].create({
                        'name': self.env['ir.sequence'].sudo().next_by_code('mrp.production.sequence'),
                        'product_id': rec.product_id.id,
                        'company_id': rec.company_id.id,
                    })
                else:
                    seq = self.env['ir.sequence'].sudo().search([('code', '=', rec.product_id.name)])
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
                    serial_id = self.env['stock.production.lot'].create({
                        'name': self.env['ir.sequence'].sudo().next_by_code(rec.product_id.name),
                        'product_id': rec.product_id.id,
                        'company_id': rec.company_id.id,
                    })
                rec.lot_producing_id = serial_id
            return super(MrpProduction, self).action_confirm()
