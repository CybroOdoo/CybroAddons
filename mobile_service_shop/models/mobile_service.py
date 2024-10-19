# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Jumana Jabin MP (odoo@cybrosys.com)
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
import pytz
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MobileService(models.Model):
    """Creates the model mobile.service"""
    _name = 'mobile.service'
    _rec_name = 'name'
    _description = "Mobile Service"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Service Number', copy=False, default="New",
                       help="Number of The Service.")
    person_name = fields.Many2one('res.partner',
                                  string="Customer Name", required=True,
                                  help="Name of the customer.")
    contact_no = fields.Char(related='person_name.mobile',
                             string="Contact Number",
                             help="Contact number of the customer.")
    email_id = fields.Char(related='person_name.email', string="Email",
                           help="Email ID of the customer.")
    street = fields.Char(related='person_name.street', string="Address",
                         help="Street of the customer.")
    street2 = fields.Char(related='person_name.street2', string="Address",
                          help="Street2 of the customer.")
    city = fields.Char(related='person_name.city', string="Address",
                       help="City of the customer.")
    state_id = fields.Many2one(related='person_name.state_id', string="Address",
                               help="State of the customer.")
    zip = fields.Char(related='person_name.zip', string="Address",
                      help="Zip number of the customer address.")
    country_id = fields.Many2one(related='person_name.country_id',
                                 string="Address",
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
        string='Service Status', default='draft', track_visibility='always',
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
                                   compute="_get_invoiced", readonly=True,
                                   copy=False, help="Invoices line")
    first_payment_inv = fields.Many2one('account.move', copy=False,
                                        help="First payment of the invoice.")
    first_invoice_created = fields.Boolean(string="First Invoice Created",
                                           invisible=True, copy=False,
                                           help="Date of the first invoice.")
    journal_type = fields.Many2one('account.journal',
                                   'Journal', invisible=True,
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
    def check_date(self):
        """Check the return date and request date"""
        if self.return_date:
            return_date_string = datetime.strptime(str(self.return_date),
                                                   "%Y-%m-%d")
            request_date_string = datetime.strptime(str(self.date_request),
                                                    "%Y-%m-%d")
            if return_date_string < request_date_string:
                raise UserError(
                    "Return date should be greater than requested date")

    def approve(self):
        """Assigning the Service Request to the corresponding user"""
        self.service_state = 'assigned'

    def complete(self):
        """Mark the service request as completed"""
        self.service_state = 'completed'

    def return_to(self):
        """The service request is returned to the client"""
        self.service_state = 'returned'

    def not_solved(self):
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
            'default_composition_mode': 'comment'}
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id.id, 'form')],
            'view_id': compose_form_id.id,
            'target': 'new',
            'context': ctx}

    def return_advance(self):
        """This method returns the current invoice related to the work"""
        inv_obj = self.env['account.move'].search(
            [('invoice_origin', '=', self.name)])
        inv_ids = []
        for each in inv_obj:
            inv_ids.append(each.id)
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
        self.invoice_count = self.env['account.move'].search_count(
            [('invoice_origin', '=', self.name)])

    @api.model
    def create(self, vals):
        """Creating sequence"""
        if 'company_id' in vals:
            vals['name'] = self.env['ir.sequence'].with_context(
                force_company=self.env.user.company_id.id).next_by_code(
                'mobile.service') or _('New')
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'mobile.service') or _('New')
        vals['service_state'] = 'draft'
        return super(MobileService, self).create(vals)

    def unlink(self):
        """Supering the unlink function"""
        for service in self:
            if service.service_state != 'draft':
                raise UserError(
                    _('You cannot delete an assigned service request'))
        return super(MobileService, self).unlink()

    def action_invoice_create_wizard(self):
        """Opening a wizard to create invoice"""
        return {
            'name': _('Create Invoice'),
            'view_mode': 'form',
            'res_model': 'mobile.invoice',
            'type': 'ir.actions.act_window',
            'target': 'new'}

    def action_post_stock(self):
        """It will post a stock picking with products in parts usage"""
        if not self.product_order_line:
            raise UserError(_('No products are mentioned for this service.'))
        flag = 0
        all_have_stock_number = True
        move_lines = []
        for order in self.product_order_line:
            if not order.stock_number:
                all_have_stock_number = False
                if order.product_uom_qty > order.qty_stock_move:
                    flag = 1
                    move_line_vals = {
                        'product_id': order.product_id.id,
                        'quantity': order.product_uom_qty - order.qty_stock_move,
                        'product_uom_id': order.product_id.uom_id.id if order.product_id.uom_id else False,
                    }
                    move_lines.append((0, 0, move_line_vals))
                elif order.product_uom_qty < order.qty_stock_move:
                    raise UserError(
                        _('Used quantity is less than quantity stock move posted.'))
        if all_have_stock_number:
            raise UserError(
                _('All products have stock moves. No stock picking will be created.'))
        if flag == 0:
            raise UserError(_('Nothing to post stock move.'))
        pick = {
            'picking_type_id': self.picking_transfer_id.id,
            'partner_id': self.person_name.id,
            'origin': self.name,
            'location_dest_id': self.person_name.property_stock_customer.id,
            'location_id': int(
                self.picking_transfer_id.default_location_src_id.id),
            'move_line_ids': move_lines
        }
        picking = self.env['stock.picking'].create(pick)
        self.stock_picking_id = picking.id
        self.picking_count = len(picking)
        picking.action_confirm()
        picking.button_validate()
        for order in self.product_order_line:
            if not order.stock_number:
                order.stock_number = picking.name
        self.message_post(
            body='Stock moves have been successfully posted for picking %s.'
                 % picking.name,)

    def action_view_invoice(self):
        """It will show the invoice for the customer"""
        self.ensure_one()
        ctx = dict(create=False)
        action = {
            'name': _("Invoices"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'target': 'current',
            'context': ctx}
        invoice_ids = self.env['account.move'].search(
            [('invoice_origin', '=', self.name)])
        inv_ids = []
        for each_ids in invoice_ids:
            inv_ids.append(each_ids.id)
        if len(invoice_ids) == 1:
            invoice = inv_ids and inv_ids[0]
            action['res_id'] = invoice
            action['view_mode'] = 'form'
            action['views'] = [
                (self.env.ref('account.view_move_form').id, 'form')]
        else:
            action['view_mode'] = 'tree,form'
            action['domain'] = [('id', 'in', inv_ids)]
        return action

    def get_ticket(self):
        """This will return a ticket associated with the given service"""
        self.ensure_one()
        user = self.env['res.users'].browse(self.env.uid)
        if user.tz:
            tz = pytz.timezone(user.tz)
            time = pytz.utc.localize(datetime.now()).astimezone(tz)
            date_today = time.strftime("%Y-%m-%d %H:%M %p")
        else:
            date_today = datetime.strftime(datetime.now(),
                                           "%Y-%m-%d %I:%M:%S %p")
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
            'mobile_brand': self.brand_name.brand_name,
            'model_name': self.model_name.mobile_brand_models}
        return self.env.ref(
            'mobile_service_shop.mobile_service_ticket').report_action(self,
                                                                       data=data)
