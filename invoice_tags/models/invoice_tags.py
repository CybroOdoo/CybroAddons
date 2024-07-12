# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
    tag_filter_id = fields.Many2one(comodel_name='ir.ui.view', string='Filter Id', help='Filter Id')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        """Inherited create method and created view for tags"""
        res = super().create(vals_list)
        inherit_id = self.env.ref('account.view_account_invoice_filter')
        arch_base = _("""<?xml version="1.0"?>
                                          <xpath expr="//filter[@name='myinvoices']"
                                            position="after">
                                            <separator/>
                                          <filter string="%s" name="%s"
                                            domain="[('invoice_tag_ids','=','%s')]"/>
                                            <separator/>
                                          </xpath>
                                          """) % (res.name, res.name, res.name)
        value = {'name': 'filter.%s' % res.name,
                 'type': 'search',
                 'model': 'account.move',
                 'mode': 'extension',
                 'inherit_id': inherit_id.id,
                 'arch_base': arch_base,
                 'active': False}
        res.tag_filter_id = self.env['ir.ui.view'].sudo().create(value).id
        return res

    def unlink(self):
        """Unlink the tags from filtering"""
        for rec in self:
            tag_name = self.env['ir.ui.view'].sudo().search([('name', '=', 'filter.%s' % rec.name)])
            tag_name.active = False
            tag_name.unlink()
        return super(InvoiceTag, self).unlink()

    def write(self, vals):
        """Change the filter name when tag changes"""
        res = super().write(vals)
        if 'name' in vals and self.tag_filter_id:
            self.tag_filter_id.arch_base = _("""<?xml version="1.0"?>
                                  <xpath expr="//filter[@name='myinvoices']"
                                    position="after">
                                    <separator/>
                                  <filter string="%s" name="%s"
                                    domain="[('invoice_tag_ids','=','%s')]"/>
                                    <separator/>
                                  </xpath>
                                  """) % (self.name, self.name, self.name)
        return res
