# -*- coding: utf-8 -*-
#############################################################################
#
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
#############################################################################
from lxml import etree

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

DEFAULT_TEMPLATE = '<div>....Enter your code here...</div>'


class InvoiceDesign(models.Model):
    """Custom invoice designs, each one backed by a QWeb view."""
    _name = 'invoice.design'
    _description = 'Invoice Design'

    name = fields.Char(required=True, help="Name of the design")
    invoice_template = fields.Text(
        string='Invoice XML', required=True,
        help='Add your customised invoice design here. Make sure that you '
             'add your code inside a <div> tag. Note: you can access the '
             'invoice data using the name "invoice"; for example, '
             '"invoice.name" gives the name of the invoice.',
        default=DEFAULT_TEMPLATE)
    view_id = fields.Many2one(
        'ir.ui.view', readonly=True, copy=False,
        ondelete='restrict',
        help="A record is created in ir.ui.view when an invoice design is "
             "created. Its id is stored in this field.")

    _name_unique = models.Constraint(
        'UNIQUE(name)',
        'Name must be unique!',
    )

    @api.model
    def _get_view_key(self, name):
        """Return the QWeb view key used for the design called ``name``."""
        return 'account.%s' % name

    @api.model
    def _check_template(self, arch):
        """Raise a UserError if ``arch`` is not a valid QWeb template."""
        try:
            etree.fromstring(arch.encode())
        except etree.XMLSyntaxError:
            raise UserError(
                self.env._('Add the template (Invoice XML) in a proper format.'))

    @api.model_create_multi
    def create(self, vals_list):
        """Create the design together with its QWeb view."""
        View = self.env['ir.ui.view'].sudo()
        for vals in vals_list:
            if not vals.get('invoice_template'):
                vals['invoice_template'] = DEFAULT_TEMPLATE
            self._check_template(vals['invoice_template'])
            try:
                view = View.create({
                    'name': vals['name'],
                    'type': 'qweb',
                    'key': self._get_view_key(vals['name']),
                    'arch': vals['invoice_template'],
                })
            except ValidationError:
                raise UserError(
                    self.env._('Add the template (Invoice XML) in a proper format.'))
            vals['view_id'] = view.id
        return super().create(vals_list)

    def write(self, vals):
        """Keep the linked QWeb view in sync with the design."""
        if 'invoice_template' in vals:
            self._check_template(vals['invoice_template'] or '')
        view_vals = {}
        if 'name' in vals:
            view_vals['name'] = vals['name']
            view_vals['key'] = self._get_view_key(vals['name'])
        if 'invoice_template' in vals:
            view_vals['arch'] = vals['invoice_template']
        if view_vals:
            try:
                self.view_id.sudo().write(view_vals)
            except ValidationError:
                raise UserError(
                    self.env._('Add the template (Invoice XML) in a proper format.'))
        return super().write(vals)

    def unlink(self):
        """Delete the linked QWeb views along with the designs."""
        views = self.view_id.sudo()
        res = super().unlink()
        views.unlink()
        return res
