# -*- coding: utf-8 -*-

##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nikhil krishnan(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import datetime
from datetime import datetime
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import Warning
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp


class MrpProduction(models.Model):
    """ Manufacturing Orders """
    _inherit = 'mrp.production'

    @api.multi
    def _indent_count(self):
        for order in self:
            indent_count = self.env['mrp.indent'].search([('origin', '=', order.id)])
            order.mrp_indent_order_count = len(indent_count)

    @api.multi
    def mrp_indent_confirm(self):
        for order in self:
            indent_id = self.env['mrp.indent'].search([('origin', '=', order.id)])
            if indent_id:
                for indent in indent_id:
                    if not indent.move_lines:
                        raise exceptions.Warning(_("Warning "
                                                   "You cannot confirm an indent %s which has no line." % indent.name))
                    else:
                        indent.write({'state': 'waiting_approval'})
                        self.indent_state = 'waiting_approval'

    @api.multi
    def action_before_assign(self):
        indent_count = self.env['mrp.indent'].search([('origin', '=', self.id)])
        if not indent_count:
            self.indent_state = 'indent_created'
            vals = {
                'origin': self.id,
                'required_date': self.date_planned_start,
                'item_for': 'mrp',
                'company_id': self.company_id.id,
            }
            indent_obj = self.env['mrp.indent'].create(vals)
            for move in self.move_raw_ids:
                move.write({'mrp_indent_id': indent_obj.id})
        else:
            if self.indent_state == 'indent_created':
                raise UserError(_("Indent already created, Please Check and Confirm your indent"))
            else:
                raise UserError(_("Indent already created, Please wait for the store team approval"))

    @api.multi
    def action_cancel(self):
        indent_ids = self.env['mrp.indent'].search([('origin', '=', self.id)])
        if indent_ids:
            for indent in indent_ids:
                indent.write({'state': 'cancel'})
        self.indent_state = 'cancel'
        return super(MrpProduction, self).action_cancel()

    mrp_indent_order_count = fields.Integer(string='# of Indent Orders', compute='_indent_count')
    indent_state = fields.Selection(
            [('draft', 'Not indented'),
             ('indent_created', 'Indent Created'),
             ('waiting_approval', 'Waiting for Approval'),
             ('done', 'Indent Approved'),
             ('cancel', 'Indent Canceled'),
             ('reject', 'Indent Rejected')], string='Indent Status', readonly=True, copy=False, default='draft')


class MrpIndent(models.Model):
    _name = "mrp.indent"

    @api.multi
    def action_assign(self):
        for production in self:
            move_to_assign = production.move_lines.filtered(lambda x: x.state in ('confirmed', 'waiting', 'assigned'))
            move_to_assign.action_assign()
            if self.origin.availability == 'assigned':
                self.issued_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.state = 'done'
                self.origin.write({'indent_state': 'done'})
        return True

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('mrp.indent') or '/'
        return super(MrpIndent, self).create(vals)

    name = fields.Char(string='name', readonly=True, copy=False)
    indent_date = fields.Datetime(string='Indent Date', required=True, default=fields.Datetime.now, readonly=True,
                                  states={'draft': [('readonly', False)]})
    required_date = fields.Datetime(string='Required Date', required=True, readonly=True, default=fields.Datetime.now,
                                    states={'draft': [('readonly', False)]})
    origin = fields.Many2one('mrp.production', string='Source Document', readonly=True, copy=False, states={'draft': [('readonly', False)]})
    issued_date = fields.Datetime(string='Approve Date', readonly=True)
    issued_by = fields.Many2one('res.users', string='Issued by', readonly=True)
    requirement = fields.Selection([('1', 'Ordinary'), ('2', 'Urgent')], 'Requirement', readonly=True, default='1',
                                   states={'draft': [('readonly', False)]})
    item_for = fields.Selection([('mrp', 'Produce'), ('other', 'Other')], string='Order for', default='other',
                                readonly=True, states={'draft': [('readonly', False)]})
    move_lines = fields.One2many('stock.move', 'mrp_indent_id', string='Moves', copy=False, readonly=True)
    product_lines = fields.One2many('mrp.indent.product.lines', 'indent_id', string='Product', copy=False)
    description = fields.Text(string='Additional Information', readonly=True,
                              states={'draft': [('readonly', False)], 'waiting_approval': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id,
                                 readonly=True, states={'draft': [('readonly', False)]})

    state = fields.Selection(
            [('draft', 'Draft'),
             ('waiting_approval', 'Waiting for Approval'),
             ('inprogress', 'Ready to Transfer'),
             ('move_created', 'Moves Created'),
             ('done', 'Done'),
             ('cancel', 'Cancel'),
             ('reject', 'Rejected')], string='State', readonly=True, default='draft', track_visibility='onchange')

    @api.multi
    def mrp_indent_confirm(self):
        for indent in self:
            if indent.item_for == 'mrp':
                if not indent.move_lines:
                    raise exceptions.Warning(_("Warning "
                                               "You cannot confirm an indent %s which has no line." % indent.name))
                else:
                    indent.write({'state': 'waiting_approval'})
                    indent.origin.write({'indent_state': 'waiting_approval'})
            else:
                if not indent.product_lines:
                    raise exceptions.Warning(_("Warning "
                                               "You cannot confirm an indent %s which has "
                                               "no product line." % indent.name))
                else:
                    indent.write({'state': 'waiting_approval'})

    @api.one
    def mrp_indent_inprogress(self):
        todo = []
        for o in self:
            if not any(line for line in o.product_lines):
                raise exceptions.Warning(_('Error!'),
                              _('You cannot Approve a order without any order line.'))

            for line in o.product_lines:
                if line:
                    todo.append(line.id)

        appr_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.env['mrp.indent.product.lines'].action_confirm(todo)

        for id in self.ids:
            self.write({'state': 'inprogress', 'issued_date': appr_date})
        return True

    @api.one
    def indent_reject(self):
        if self.move_lines:
            for line in self.move_lines:
                if line.state == 'cancel':
                    pass
                elif line.state == 'done':
                    pass
                else:
                    line.action_cancel()
        self.write({'state': 'reject'})
        if self.origin:
            self.origin.action_cancel()

    @api.multi
    def indent_transfer(self):
        name = self.name
        move_lines_obj = self.env['stock.move']
        if self.product_lines:
            for line in self.product_lines:
                if line.product_id.type != 'service':
                    if line.location_id:
                        if line.location_dest_id:
                            tot_qty = 0
                            obj_quant = self.env['stock.quant'].search([('product_id', '=', line.product_id.id),
                                                                        ('location_id', '=', line.location_id.id)])
                            for obj in obj_quant:
                                tot_qty += obj.qty
                            move_line = {}
                            if line.product_id.type == 'consu':
                                move_line = {
                                    'product_id': line.product_id.id,
                                    'state': "draft",
                                    'product_uom_qty': line.product_uom_qty,
                                    'product_uom': line.product_id.uom_id.id,
                                    'name': line.product_id.name,
                                    'location_id': line.location_id.id,
                                    'location_dest_id': line.location_dest_id.id,
                                    'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    'date_expected': self.required_date,
                                    'invoice_state': "none",
                                    'origin': name,
                                    'mrp_indent_id': self.id
                                }
                                move_lines_obj.create(move_line)
                            else:
                                move_line = {}
                                if tot_qty >= line.product_uom_qty:
                                    move_line = {
                                                'product_id': line.product_id.id,
                                                'state': "draft",
                                                'product_uom_qty': line.product_uom_qty,
                                                'product_uom': line.product_id.uom_id.id,
                                                'name': line.product_id.name,
                                                'location_id': line.location_id.id,
                                                'location_dest_id': line.location_dest_id.id,
                                                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                'date_expected': self.required_date,
                                                'invoice_state': "none",
                                                'origin': name,
                                                'mrp_indent_id': self.id
                                                }
                                    move_lines_obj.create(move_line)
                                else:
                                    if tot_qty:
                                        raise exceptions.Warning((" No sufficient stock for product ' %s ' in '%s'.  "
                                                                  "Available quantity is %s %s.") %
                                                                 (line.product_id.name, line.location_id.name, tot_qty,
                                                                  line.product_uom.name))
                                    else:
                                        raise exceptions.Warning(
                                                      (" No stock for product ' %s ' in '%s'."
                                                       "  Please continue with another location ") % (line.product_id.name,
                                                                                                      line.location_id.name))
                        else:
                            raise exceptions.Warning((" Destination Location is not set properly for' %s '. "
                                                      "So Plese cancel this indent and create a new one please.")
                                                     % line.product_id.name)
                    else:
                        raise exceptions.Warning(("Source Location is not set properly for ' %s '.  "
                                                  "Please go and set Source Location.")
                                                 % line.product_id.name)
                else:
                    raise exceptions.Warning("This product is a service type product.")
        else:
            raise exceptions.Warning('You cannot Transfer a order without any product line.')
        self.write({'state': 'move_created'})

    @api.multi
    def indent_transfer_move_confirm(self):
        if self.move_lines:
            for line in self.move_lines:
                if line.state == 'cancel':
                    pass
                elif line.state == 'done':
                    pass
                else:
                    line.action_done()
        else:
            raise Warning(_('Error!'),
                          _('You cannot Confirm a order without any move lines.'))
        self.write({'state': 'done'})


class IndentProductLines(models.Model):
    _name = 'mrp.indent.product.lines'
    _description = 'Indent Product Lines'

    @api.one
    def action_confirm(self, todo):
        self.write({'state': 'inprogress'})
        return True

    indent_id = fields.Many2one('mrp.indent', string='Indent', required=True, ondelete='cascade')
    name = fields.Text(string='Description', required=True, readonly=True,
                       states={'draft': [('readonly', False)], 'waiting_approval': [('readonly', False)]})
    product_id = fields.Many2one('product.product', string='Product', required=True, readonly=True,
                                 states={'draft': [('readonly', False)], 'waiting_approval': [('readonly', False)]})
    original_product_id = fields.Many2one('product.product', string='Product to be Manufactured', readonly=True,
                                          states={'draft': [('readonly', False)], 'waiting_approval': [('readonly', False)]})
    product_uom_qty = fields.Float(string='Quantity Required', digits_compute=dp.get_precision('Product UoS'), required=True,
                                   readonly=True, states={'draft': [('readonly', False)],
                                                          'waiting_approval': [('readonly', False)],
                                                          'inprogress': [('readonly', False)]})
    product_uom = fields.Many2one('product.uom', string='Unit of Measure', required=True, readonly=True,
                                  states={'draft': [('readonly', False)], 'waiting_approval': [('readonly', False)],
                                          'inprogress': [('readonly', False)]})
    location_id = fields.Many2one('stock.location', string='Source Location', readonly=True,
                                  states={'inprogress': [('readonly', False)]})
    location_dest_id = fields.Many2one('stock.location', string='Destination Location', required=True, readonly=True,
                                       states={'draft': [('readonly', False)],
                                               'waiting_approval': [('readonly', False)]})

    delay = fields.Float(string='Lead Time')
    purpose = fields.Text(string='Purpose')
    state = fields.Selection(
            [('draft', 'Draft'),
             ('waiting_approval', 'Waiting for Approval'),
             ('inprogress', 'Ready to Transfer'),
             ('move_created', 'Moves Created'),
             ('done', 'Done'),
             ('cancel', 'Cancel'),
             ('reject', 'Rejected')], string='State', default='draft', related='indent_id.state')

    sequence = fields.Integer('Sequence')

    def onchange_product_id(self, product_id=False, product_uom_qty=0.0, product_uom=False, name=''):
        product_obj = self.env['product.product']
        value = {}
        if not product_id:
            return {'value': {'product_uom_qty': 1.0, 'product_uom': False,
                              'name': '', 'specification': '', 'delay': 0.0}}

        product = product_obj.browse(product_id)
        value['name'] = product.name_get()[0][1]
        value['product_uom'] = product.uom_id.id
        value['specification'] = product.name_get()[0][1]

        return {'value': value}


class StockMove(models.Model):
    _inherit = 'stock.move'

    mrp_indent_id = fields.Many2one('mrp.indent', 'Indent')
