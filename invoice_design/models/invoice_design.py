# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
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
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class InvoiceDesign(models.Model):
    """Details of model 'invoice.design'"""
    _name = 'invoice.design'
    _description = 'Invoice Design'

    name = fields.Char(string='Name', help="Name of the design")
    invoice_template = fields.Text(string='Invoice XML',
                                   help='Add your customised invoice design '
                                        'here. Make sure that you add code '
                                        'inside <div> tag. Note: You can '
                                        'access data of invoice using name '
                                        '"invoice", ie, "invoice.name" will '
                                        'give you the name of invoice ',
                                   default='<div>'
                                           '....Enter your code here...'
                                           '</div>')
    view_id = fields.Many2one('ir.ui.view', string="View",
                              help="A record will be created in ir.ui.view "
                                   "on creating a record in invoice design. "
                                   "Its id is stored in this field")
    _sql_constraints = [('unique_name', 'UNIQUE(name)', 'Name must be unique!')]

    @api.model
    def create(self, vals):
        """On creating a record in 'invoice.design', a new record will be
         created in 'ir.ui.view'"""
        try:
            view = self.env['ir.ui.view'].create({
                'name': vals['name'],
                'type': 'qweb',
                'key': 'account.{}'.format(vals['name']),
                'arch': vals['invoice_template'],
            })
            vals.update({
                'view_id': view.id,
            })
            return super(InvoiceDesign, self).create(vals)
        except Exception:
            raise UserError(
                _('Add the template (Invoice XML) in proper format.'))

    def write(self, vals):
        """On editing a record in 'invoice.design', corresponding record
        created in 'ir.ui.view' will also be edited"""
        try:
            view = self.env['ir.ui.view'].browse(self.view_id.id)
            for key in list(vals.keys()):
                if key == 'name':
                    view.write({'name': vals['name']})
                if key == 'invoice_template':
                    view.write({'arch': vals['invoice_template']})
            return super(InvoiceDesign, self).write(vals)
        except Exception:
            raise UserError(
                _('Add the template (Invoice XML) in proper format.'))

    def unlink(self):
        """On deleting a record in 'invoice.design', corresponding record
        created in 'ir.ui.view' will also be deleted"""
        for rec in self:
            view = self.env['ir.ui.view'].browse(rec.view_id.id)
            view.unlink()
        return super(InvoiceDesign, self).unlink()
