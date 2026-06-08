# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Surya Gayathry TA (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    """Inherits stock.picking"""
    _inherit = 'stock.picking'

    barcode = fields.Char(string='Barcode', help="Product barcode")
    invoice_count = fields.Integer(string='Invoices',
                                   compute='_compute_invoice_count',
                                   help="Count of invoices")
    operation_code = fields.Selection(string="Operation code",
                                      related='picking_type_id.code',
                                      help="Operation code")
    is_return = fields.Boolean(string="Is return picking",
                               help="is this a return picking")
    invoice_created = fields.Boolean(string='Invoice Created')

    def _get_invoice_line_account(self, product, move_type):
        """Return the product account required by account.move.line."""
        accounts = product.product_tmpl_id.get_product_accounts()
        account = accounts['expense'] if move_type in ('in_invoice', 'in_refund') \
            else accounts['income']
        if not account:
            raise UserError(_("Please configure an account for the product."))
        return account

    @api.onchange('barcode')
    def _onchange_barcode(self):
        """Scanning the barcode"""
        match = False
        product_obj = self.env['product.product']
        product_id = product_obj.search(
            [('barcode', '=', self.barcode)], limit=1)

        if self.barcode and not product_id:
            return {'warning': {
                'title': _('Warning !'),
                'message': _('No product is available for this barcode')
            }}

        if self.barcode and self.move_line_ids:
            for line in self.move_line_ids:
                if line.product_id.barcode == self.barcode:
                    line.quantity += 1
                    match = True
                    break  # stop after first match

        if self.barcode and not match and product_id:
            return {'warning': {
                'title': _('Warning !'),
                'message': _(
                    'This product is not available in the order. '
                    'You can add it by clicking "Add a line" and scan.'
                )
            }}

    def write(self, vals):
        """Write values to order line"""
        res = super(StockPicking, self).write(vals)
        if vals.get('barcode') and self.move_ids:
            for line in self.move_ids:
                if line.product_id.barcode == vals['barcode']:
                    # Using a context flag to prevent multiple increments
                    if self.env.context.get('barcode_processed'):
                        line.with_context(barcode_processed=False).write(
                            {'product_uom_qty': line.product_uom_qty + 1})
        return res

    def _compute_invoice_count(self):
        """This computes function used to count the number of invoice
        for the picking"""
        for picking_id in self:
            move_ids = picking_id.env['account.move'].search(
                [('invoice_origin', '=', picking_id.name)])
            if move_ids:
                self.invoice_count = len(move_ids)
            else:
                self.invoice_count = 0

    def action_create_invoice(self):
        """This is the function for creating customer invoice
        from the picking"""
        for picking_id in self:
            current_user = self.env.uid
            if picking_id.picking_type_id.code == 'outgoing':
                customer_journal_id = picking_id.env[
                                          'ir.config_parameter'].sudo().get_param(
                    'stock_move_invoice.customer_journal_id') or False
                if not customer_journal_id:
                    raise UserError(
                        _("Please configure the journal from settings"))
                invoice_line_list = []
                for move in picking_id.move_ids:
                    vals = (0, 0, {
                        'name': move.description_picking,
                        'product_id': move.product_id.id,
                        'price_unit': move.product_id.lst_price,
                        'account_id': picking_id._get_invoice_line_account(
                            move.product_id, 'out_invoice').id,
                        'tax_ids': [(6, 0, [
                            picking_id.company_id.account_sale_tax_id.id])],
                        'quantity': move.quantity,
                    })
                    invoice_line_list.append(vals)
                    invoice = picking_id.env['account.move'].create({
                        'move_type': 'out_invoice',
                        'invoice_origin': picking_id.name,
                        'invoice_user_id': current_user,
                        'narration': picking_id.name,
                        'partner_id': picking_id.partner_id.id,
                        'currency_id': picking_id.env.user.company_id.
                        currency_id.id,
                        'journal_id': int(customer_journal_id),
                        'payment_reference': picking_id.name,
                        'picking_id': picking_id.id,
                        'invoice_line_ids': invoice_line_list,
                        'transfer_created': True
                    })
                    return invoice

    def action_create_bill(self):
        """This is the function for creating vendor bill
                from the picking"""
        for picking_id in self:
            current_user = self.env.uid
            if picking_id.picking_type_id.code == 'incoming':
                vendor_journal_id = picking_id.env[
                                        'ir.config_parameter'].sudo().get_param(
                    'stock_move_invoice.vendor_journal_id') or False
                if not vendor_journal_id:
                    raise UserError(
                        _("Please configure the journal from the settings."))
                invoice_line_list = []
                for move in picking_id.move_ids:
                    vals = (0, 0, {
                        'name': move.description_picking,
                        'product_id': move.product_id.id,
                        'price_unit': move.product_id.
                            lst_price,
                        'account_id': picking_id._get_invoice_line_account(
                            move.product_id, 'in_invoice').id,
                        'tax_ids': [(6, 0, [
                            picking_id.company_id.account_purchase_tax_id.id])],
                        'quantity': move.quantity,
                    })
                    invoice_line_list.append(vals)
                    invoice = picking_id.env['account.move'].create({
                        'move_type': 'in_invoice',
                        'invoice_origin': picking_id.name,
                        'invoice_user_id': current_user,
                        'narration': picking_id.name,
                        'partner_id': picking_id.partner_id.id,
                        'currency_id': picking_id.env.user.company_id.
                        currency_id.id,
                        'journal_id': int(vendor_journal_id),
                        'payment_reference': picking_id.name,
                        'picking_id': picking_id.id,
                        'invoice_line_ids': invoice_line_list,
                        'transfer_created': True
                    })
                    return invoice

    def action_create_customer_credit(self):
        """This is the function for creating customer credit note
                from the picking"""
        for picking_id in self:
            current_user = picking_id.env.uid
            if picking_id.picking_type_id.code == 'incoming':
                customer_journal_id = picking_id.env[
                                          'ir.config_parameter'].sudo() \
                                          .get_param(
                    'stock_move_invoice.customer_journal_id') or False
                if not customer_journal_id:
                    raise UserError(
                        _("Please configure the journal from settings"))
                invoice_line_list = []
                for move in picking_id.move_ids:
                    vals = (0, 0, {
                        'name': move.description_picking,
                        'product_id': move.product_id.id,
                        'price_unit': move.product_id.
                            lst_price,
                        'account_id': picking_id._get_invoice_line_account(
                            move.product_id, 'out_refund').id,
                        'tax_ids': [(6, 0, [
                            picking_id.company_id.account_sale_tax_id.id])],
                        'quantity': move.quantity,
                    })
                    invoice_line_list.append(vals)
                    invoice = picking_id.env['account.move'].create({
                        'move_type': 'out_refund',
                        'invoice_origin': picking_id.name,
                        'invoice_user_id': current_user,
                        'narration': picking_id.name,
                        'partner_id': picking_id.partner_id.id,
                        'currency_id': picking_id.env.user.company_id.
                        currency_id.id,
                        'journal_id': int(customer_journal_id),
                        'payment_reference': picking_id.name,
                        'picking_id': picking_id.id,
                        'invoice_line_ids': invoice_line_list
                    })
                    return invoice

    def action_create_vendor_credit(self):
        """This is the function for creating refund
                from the picking"""
        for picking_id in self:
            current_user = self.env.uid
            if picking_id.picking_type_id.code == 'outgoing':
                vendor_journal_id = picking_id.env[
                                        'ir.config_parameter'].sudo().get_param(
                    'stock_move_invoice.vendor_journal_id') or False
                if not vendor_journal_id:
                    raise UserError(
                        _("Please configure the journal from the settings."))
                invoice_line_list = []
                for move in picking_id.move_ids:
                    vals = (0, 0, {
                        'name': move.description_picking,
                        'product_id': move.product_id.id,
                        'price_unit': move.product_id.
                            lst_price,
                        'account_id': picking_id._get_invoice_line_account(
                            move.product_id, 'in_refund').id,
                        'tax_ids': [(6, 0, [
                            picking_id.company_id.account_purchase_tax_id.id])],
                        'quantity': move.quantity,
                    })
                    invoice_line_list.append(vals)
                    invoice = picking_id.env['account.move'].create({
                        'move_type': 'in_refund',
                        'invoice_origin': picking_id.name,
                        'invoice_user_id': current_user,
                        'narration': picking_id.name,
                        'partner_id': picking_id.partner_id.id,
                        'currency_id': picking_id.env.user.company_id.
                        currency_id.id,
                        'journal_id': int(vendor_journal_id),
                        'payment_reference': picking_id.name,
                        'picking_id': picking_id.id,
                        'invoice_line_ids': invoice_line_list
                    })
                    return invoice

    def action_open_picking_invoice(self):
        """This is the function of the smart button which redirect to the
        invoice related to the current picking"""
        return {
            'name': 'Invoices',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [('picking_id', '=', self.id)],
            'context': {'create': False},
            'target': 'current'
        }

    @api.model
    def get_operation_types(self):
        """rpc method of operation type tiles,operation type graph
            Returns operation type details.
            no_transfer - each operation type transfer count,
            late - each operation type late count
            waiting - each operation type waiting count
            operation_type_name - have all the operation type name
            backorder - each operation type backorders count
                """
        no_transfer = {}
        stock_picking_type = self.env['stock.picking.type'].search([])
        stock_picking = self.env['stock.picking'].search([])
        stock = []
        length = []
        names = []
        late = {}
        query = '''select stock_picking.picking_type_id, count(stock_picking.
        picking_type_id) from stock_picking
            inner join stock_picking_type on stock_picking.picking_type_id = 
            stock_picking_type.id
            where stock_picking.company_id = %s and
            stock_picking.state in ('assigned', 'waiting', 'confirmed') and 
            (has_deadline_issue = true or 
            date_deadline <= now() or scheduled_date <= now())
            group by stock_picking.picking_type_id''' % self.env.company.id
        self.env.cr.execute(query)
        lates = self.env.cr.dictfetchall()
        for rec in lates:
            late.update({rec.get('picking_type_id'): rec.get('count')})
        waiting = {}
        backorder = {}
        operation_type_name = {}
        for type in stock_picking_type:
            names.append(type.name)
            orders = stock_picking.filtered(
                lambda r: r.picking_type_id.id == type.id)
            stock.append(len(orders))
            length_stock_picking = len(orders)
            length.append(len(stock_picking.filtered(
                lambda r: r.picking_type_id.id == type.id)))
            no_transfer.update({type.id: length_stock_picking})
            operation_type_name.update({type.id: type.name})
            if len(orders) > 0:
                if len(orders.filtered(lambda r: r.state == 'confirmed')) > 0:
                    waiting.update({type.id: len(
                        orders.filtered(lambda r: r.state == 'confirmed'))})
                if len(orders.mapped('backorder_id')) > 0:
                    backorder.update(
                        {type.id: len(orders.mapped('backorder_id'))})
        return no_transfer, late, waiting, operation_type_name, backorder

    @api.model
    def get_product_category(self):
        """rpc method of product category graph
        Returns product categories and category having on hand product quantity"""
        category_ids = self.env['product.category'].search([])
        category_name = []
        product_count = []
        for rec in category_ids:
            name = rec.name
            category_name.append(name)
            count = rec.product_count
            product_count.append(count)
        value = {'name': category_name, 'count': product_count}
        return value

    @api.model
    def get_locations(self):
        """rpc method of product location table
               Returns locations and location having on hand product quantity"""
        stock_quant_ids = self.env['stock.quant'].search([])
        locations = stock_quant_ids.mapped('location_id')
        value = {}
        for rec in locations:
            loc_stock_quant = stock_quant_ids.filtered(
                lambda x: x.location_id == rec)
            on_hand_quantity = sum(
                loc_stock_quant.mapped('inventory_quantity_auto_apply'))
            value[rec.name] = on_hand_quantity
        return value
