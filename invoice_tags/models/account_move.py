# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from odoo import fields, models, api, _


class AccountMove(models.Model):
    """Add field for tags in account.move"""
    _inherit = 'account.move'

    invoice_tag_ids = fields.Many2many('invoice.tag', string="Tags",
                                       help="Field for adding tags in invoice")

    @api.onchange('invoice_tag_ids')
    def _onchange_tag_filter(self):
        """Create filtering option dynamically in accordance with tags that
        are added to invoices"""
        linked_tags = [tag for tag in self.search(
            [('id', '!=', self._origin.id)]).invoice_tag_ids]
        for result in self.invoice_tag_ids._origin:
            if result not in linked_tags:
                linked_tags.append(result)
            if not self.env['ir.ui.view'].sudo().search(
                    [('name', '=', f'filter.{result.name}')]):
                inherit_id = self.env.ref('account.view_account_invoice_filter')
                arch_base = _("""<?xml version="1.0"?>
                                  <xpath expr="//filter[@name='myinvoices']"
                                    position="after">
                                    <separator/>
                                  <filter string="%s" name="%s"
                                    domain="[('invoice_tag_ids','=','%s')]"/>
                                    <separator/>
                                  </xpath>
                                  """) % (result.name, result.name, result.name)
                value = {'name': f'filter.{result.name}',
                         'type': 'search',
                         'model': 'account.move',
                         'mode': 'extension',
                         'inherit_id': inherit_id.id,
                         'arch_base': arch_base,
                         'active': True}
                self.env['ir.ui.view'].sudo().create(value)
        # we need to unlink from the view if the tags are removed from invoice
        for tags in self.invoice_tag_ids.search([]):
            if tags not in linked_tags:
                self.env['ir.ui.view'].sudo().search(
                    [('name', '=', f'filter.{tags.name}')]).active = False
                self.env['ir.ui.view'].sudo().search(
                    [('name', '=', f'filter.{tags.name}')]).unlink()
