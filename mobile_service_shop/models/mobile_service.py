# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anupriya Ashok (odoo@cybrosys.com)
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
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models
from odoo.exceptions import UserError


class MobileService(models.Model):
    """Creates the model mobile.service"""
    _name = 'mobile.service'
    _description = "Mobile Service"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Service Number', copy=False, default="New",
                       help="Number of The Service.")
    person_name = fields.Many2one('res.partner',
                                  string="Customer Name", required=True,
                                  help="Name of the customer.")
    contact_no = fields.Char(related='person_name.phone',
                             string="Contact Number", store=True,
                             help="Contact number of the customer.")
    email_id = fields.Char(related='person_name.email', string="Email",
                           help="Email ID of the customer.")
    street = fields.Char(related='person_name.street', help="Street of the customer.")
    street2 = fields.Char(related='person_name.street2',
                          help="Street2 of the customer.")
    city = fields.Char(related='person_name.city',
                       help="City of the customer.")
    state_id = fields.Many2one(related='person_name.state_id',
                               help="State of the customer.")
    zip = fields.Char(related='person_name.zip',
                      help="Zip number of the customer address.")
    country_id = fields.Many2one(related='person_name.country_id',
                                 help="Country of the customer.")
    brand_name = fields.Many2one('mobile.brand',
                                 string="Mobile Brand",
                                 help="Brand name of the mobile.")
    is_in_warranty = fields.Boolean(
        'In Warranty', default=False,
        help="Specify if the product is in warranty.")
    warranty_number = fields.Char(string="Warranty No ",
                                  help="Warranty details.")
    re_repair = fields.Boolean('Re-repair', default=False,
                               help="Re-repairing.")
    imei_no = fields.Char(string="IMEI Number",
                          help="IMEI Number of the device.")
    model_name = fields.Many2one('brand.model', string="Model",
                                 domain="[('mobile_brand_name','=',brand_name)]"
                                 , help="Model name of the device.")
    image_medium = fields.Binary(related='model_name.image_medium', store=True,
                                 attachment=True, help="Image of the device.")
    date_request = fields.Date(string="Requested Date",
                               default=fields.Date.context_today,
                               help="Device submitted date.")
    return_date = fields.Date(string="Return Date", required=True,
                              help="Device returned date.")
    technician_name = fields.Many2one('res.users',
                                      string="Technician Name",
                                      default=lambda self: self.env.user,
                                      help="Work assigned technician name.",
                                      required=True)
    service_state = fields.Selection(
        [('draft', 'Draft'), ('assigned', 'Assigned'),
         ('completed', 'Completed'), ('returned', 'Returned'),
         ('not_solved', 'Not solved')],
        string='Service Status', default='draft', tracking=True,
        help='Service status of the work.')
    complaints_tree = fields.One2many('mobile.complaint.tree',
                                      'complaint_id',
                                      string='Complaints Tree',
                                      help='Mobile complaint details.')
    product_order_line = fields.One2many('product.order.line',
                                         'product_order_id',
                                         string='Parts Order Lines',
                                         help='Product parts order details.')
    internal_notes = fields.Text(string="Internal Notes")
    invoice_count = fields.Integer(compute='_compute_invoice_count',
                                   string='# Invoice', copy=False,
                                   help="Count of invoice.")
    invoice_ids = fields.Many2many("account.move", string='Invoices',
                                   compute="_get_invoiced",
                                   copy=False, help="Invoices line")
    first_payment_inv = fields.Many2one('account.move', copy=False,
                                        help="First payment of the invoice.")
    first_invoice_created = fields.Boolean(string="First Invoice Created",copy=False,
                                           help="Date of the first invoice.")
    journal_type = fields.Many2one('account.journal',
                                   'Journal',
                                   default=lambda self: self.env[
                                       'account.journal'].search(
                                       [('code', '=', 'SERV')]),
                                   help='Type of the journal.')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.company,
                                 help='Default company id.')

    @api.model
    def _default_picking_transfer(self):
        """To get the default picking transfers."""
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get(
            'company_id') or self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'outgoing'),
                                 ('warehouse_id.company_id', '=', company_id)],
                                limit=1)
        if not types:
            types = type_obj.search([('code', '=', 'outgoing'),
                                     ('warehouse_id', '=', False)])
        return types[:4]
    stock_picking_id = fields.Many2one('stock.picking',
                                       string="Picking Id",
                                       help='Stock picking ID information.')
    picking_transfer_id = fields.Many2one('stock.picking.type',
                                          string='Deliver To',
                                          required=True,
                                          default=_default_picking_transfer,
                                          help="This will determine picking "
                                               "type of outgoing shipment.")
    picking_count = fields.Integer(string="Picking Count",
                                   help='Number of outgoing shipment')

    @api.onchange('return_date')
    def _onchange_return_date(self):
        """Check the return date and request date"""
        if self.return_date:
            if self.return_date < self.date_request:
                raise UserError("Return date should be greater than requested date")

    def action_approve(self):
        """Assigning the Service Request to the corresponding user"""
        self.service_state = 'assigned'

    def action_complete(self):
        """Mark the service request as completed"""
        self.service_state = 'completed'

    def action_return_to(self):
        """The service request is returned to the client"""
        for record in self:
            record.write({
                'service_state': 'returned',
                'return_date': fields.Date.today()
            })

    def action_not_solved(self):
        """Mark the service request as not solved"""
        self.service_state = 'not_solved'

    def action_send_mail(self):
        """This function opens a window to compose an email, with the edi sale
        template message loaded by default"""
        self.ensure_one()
        try:
            template_id = self.env.ref(
                'mobile_service_shop.email_template_mobile_service')
        except ValueError:
            template_id = False
        try:
            compose_form_id = self.env.ref(
                'mail.email_compose_message_wizard_form')
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'mobile.service',
            'default_res_ids': self.ids,
            'default_use_template': bool(template_id),
            'default_template_id': template_id.id,
            'default_composition_mode': 'comment',
            'default_partner_ids': [(4, self.person_name.id)] if self.person_name else [],
        }
        return {
            'name': ('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id.id, 'form')],
            'view_id': compose_form_id.id,
            'target': 'new',
            'context': ctx}

    def action_return_advance(self):
        """This method returns the current invoice related to the work"""
        inv_obj = self.env['account.move'].search(
            [('invoice_origin', '=', self.name)])
        inv_ids = inv_obj.ids
        view_id = self.env.ref('account.view_move_form').id
        if inv_ids:
            if len(inv_ids) <= 1:
                value = {
                    'view_mode': 'form',
                    'res_model': 'account.move',
                    'view_id': view_id,
                    'type': 'ir.actions.act_window',
                    'name': 'Invoice',
                    'res_id': inv_ids[0]}
            else:
                value = {
                    'domain': str([('id', 'in', inv_ids)]),
                    'view_mode': 'tree,form',
                    'res_model': 'account.move',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name': 'Invoice',
                    'res_id': inv_ids[0]}
            return value
        else:
            raise UserError("No invoice created")

    def _compute_invoice_count(self):
        """Calculating the number of invoices"""
        for record in self:
            record.invoice_count = self.env['account.move'].search_count(
                [('invoice_origin', '=', record.name)])

    @api.model_create_multi
    def create(self, vals_list):
        """Creating sequence"""
        for vals in vals_list:
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(
                    with_company=vals['company_id']
                    ).next_by_code('mobile.service') or ('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'mobile.service') or ('New')
            vals['service_state'] = 'draft'
        return super(MobileService, self).create(vals_list)

    def unlink(self):
        """Supering the unlink function"""
        for service in self:
            if service.service_state != 'draft':
                raise UserError('You cannot delete an assigned service request')
        return super(MobileService, self).unlink()

    def action_invoice_create_wizard(self):
        """Opening a wizard to create invoice"""
        return {
            'name': ('Create Invoice'),
            'view_mode': 'form',
            'res_model': 'mobile.invoice.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

    def action_post_stock(self):
        """It will post a stock picking with products in parts usage"""
        if not self.product_order_line:
            raise UserError('No products are mentioned for this service.')
        
        move_lines = []
        lines_to_update = []
        for order in self.product_order_line:
            if not order.stock_number and order.product_uom_qty > order.qty_stock_move:
                qty_to_move = order.product_uom_qty - order.qty_stock_move
                move_lines.append((0, 0, {
                    'product_id': order.product_id.id,
                    'product_uom_qty': qty_to_move,
                    'product_uom': order.product_id.uom_id.id if order.product_id.uom_id else False,
                    'location_id': self.picking_transfer_id.default_location_src_id.id,
                    'location_dest_id': self.person_name.property_stock_customer.id,
                }))
                lines_to_update.append((order, qty_to_move))

        if not move_lines:
            raise UserError('Nothing to post stock move or all products already have stock moves.')

        pick = {
            'picking_type_id': self.picking_transfer_id.id,
            'partner_id': self.person_name.id,
            'origin': self.name,
            'location_dest_id': self.person_name.property_stock_customer.id,
            'location_id': self.picking_transfer_id.default_location_src_id.id,
            'move_ids': move_lines
        }
        picking = self.env['stock.picking'].create(pick)
        self.stock_picking_id = picking.id
        self.picking_count = len(picking)
        picking.action_confirm()
        picking.action_assign()
        
        # Force "Done" quantities and "Picked" status for Odoo 19 automation
        for move in picking.move_ids:
            move.write({
                'quantity': move.product_uom_qty,
                'picked': True
            })
            
        # Validate skipping backorder/immediate wizards
        picking.with_context(cancel_backorder=True)._action_done()
        
        for order, qty in lines_to_update:
            order.write({
                'stock_number': picking.name,
                'qty_stock_move': order.qty_stock_move + qty
            })
            
        self.message_post(
            body='Stock moves have been successfully posted for picking %s.'
                 % picking.name,)

    def action_view_invoice(self):
        """It will show the invoice for the customer"""
        self.ensure_one()
        invoice_ids = self.env['account.move'].search(
            ['|',('invoice_origin', '=', self.name),('reversed_entry_id.invoice_origin', '=', self.name)])
        inv_ids = invoice_ids.ids
        action = {
            'name': ("Invoices"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'target': 'current',
            'context': {'create': False},
            'domain': [('id', 'in', inv_ids)],
        }
        if len(inv_ids) > 1:
            action['view_mode'] = 'list,form'
            action['views'] = [
                (self.env.ref('account.view_move_tree').id, 'list'),
                (self.env.ref('account.view_move_form').id, 'form')
            ]
        elif len(inv_ids) == 1:
            action['view_mode'] = 'form'
            action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
            action['res_id'] = inv_ids[0]
        else:
            return {'type': 'ir.actions.act_window_close'}
        return action

    def action_get_ticket(self):
        """This will return a ticket associated with the given service"""
        self.ensure_one()
        now_utc = fields.Datetime.now()
        now_local = fields.Datetime.context_timestamp(self, now_utc)
        date_today = now_local.strftime("%Y-%m-%d %H:%M %p")
        complaint_text = ""
        description_text = ""
        complaint_id = self.env['mobile.complaint.tree'].search(
            [('complaint_id', '=', self.id)])
        if complaint_id:
            for obj in complaint_id:
                complaint = obj.complaint_type_tree
                description = obj.description_tree
                complaint_text = complaint.complaint_type + ", " + complaint_text
                if description.description:
                    description_text = description.description + ", " + description_text
        else:
            for obj in complaint_id:
                complaint = obj.complaint_type_tree
                complaint_text = complaint.complaint_type + ", " + complaint_text
        data = {
            'ids': self.ids,
            'model': self._name,
            'date_today': date_today,
            'date_request': self.date_request,
            'date_return': self.return_date,
            'sev_id': self.name,
            'warranty': self.is_in_warranty,
            'customer_name': self.person_name.name,
            'imei_no': self.imei_no,
            'technician': self.technician_name.name,
            'complaint_types': complaint_text,
            'complaint_description': description_text,
            'mobile_brand': self.brand_name.display_name if self.brand_name else '',
            'model_name': self.model_name.display_name if self.model_name else '',
            }
        return self.env.ref(
            'mobile_service_shop.mobile_service_ticket').report_action(self,
                                                                       data=data)

    def _get_invoiced(self):
        """Compute the invoices linked to this service record"""
        for record in self:
            record.invoice_ids = self.env['account.move'].search(
                ['|',
                 ('invoice_origin', '=', record.name),
                 ('reversed_entry_id.invoice_origin', '=', record.name)
                 ])