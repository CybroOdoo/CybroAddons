# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Saneen K (odoo@cybrosys.com)
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
from random import randint
from odoo import api, fields, models, _


class InvoiceTag(models.Model):
    """class for creating tags"""
    _name = "invoice.tag"
    _description = "Invoice Tag"

    def _get_default_color(self):
        """function to select color for tags"""
        return randint(1, 11)

    name = fields.Char(string='Tag Name', required=True, translate=True, help="Invoice tags")
    color = fields.Integer(string='Color', default=_get_default_color, help="Tag color")

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]

    @api.model
    def create(self, vals):
        """Create filtering option in accordance with tags that are created"""
        result = super(InvoiceTag, self).create(vals)
        inherit_id = self.env.ref('account.view_account_invoice_filter')
        arch_base = _("""<?xml version="1.0"?>
                          <xpath expr="//filter[@name='draft']"
                            position="before">
                            <separator/>
                          <filter string="%s" name="%s"
                            domain="[('invoice_tag_ids','=','%s')]"/>
                            <separator/>
                          </xpath>
                          """) % (result.name, result.name, result.name)
        value = {'name': 'filter.%s' % result.name,
                 'type': 'search',
                 'model': 'account.move',
                 'mode': 'extension',
                 'inherit_id': inherit_id.id,
                 'arch_base': arch_base,
                 'active': True}
        self.env['ir.ui.view'].sudo().create(value)
        return result

    def unlink(self):
        """Unlink the tags from filtering"""
        for rec in self:
            tag_name = self.env['ir.ui.view'].sudo().search([('name', '=', 'filter.%s' % rec.name)])
            tag_name.active = False
            tag_name.unlink()
        return super(InvoiceTag, self).unlink()
