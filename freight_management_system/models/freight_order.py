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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import Command, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare, float_is_zero


class FreightOrder(models.Model):
    """Model for creating freight orders"""
    _name = 'freight.order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Freight Order'

    name = fields.Char(default='New', readonly=True,
                       tracking=True, help='Name of the order')
    shipper_id = fields.Many2one('res.partner', required=True,
                                 tracking=True, help="Shipper's Details")
    consignee_id = fields.Many2one('res.partner',
                                   tracking=True,
                                   help="Select the consignee for the order")
    type = fields.Selection([('import', 'Import'), ('export', 'Export')],
                            string='Import/Export', required=True,
                            tracking=True, help="Type of freight operation")
    transport_type = fields.Selection([('land', 'Land'), ('air', 'Air'),
                                       ('water', 'Water')], string='Transport',
                                      tracking=True,
                                      help='Type of transportation',
                                      required=True)
    land_type = fields.Selection(
        [('ltl', 'LTL'), ('ftl', 'FTL')],
        string='Land Shipping',
        tracking=True,
        help="Types of shipment movement involved in land")
    water_type = fields.Selection(
        [('fcl', 'FCL'), ('lcl', 'LCL')],
        string='Water Shipping',
        tracking=True,
        help="Types of shipment movement involved in water")
    order_date = fields.Date(
        string='Date', default=fields.Date.context_today,
        tracking=True, help="Date of order")
    loading_port_id = fields.Many2one(
        'freight.port', required=True, tracking=True,
        help="Loading port of the freight order")
    discharging_port_id = fields.Many2one(
        'freight.port',
        required=True, tracking=True,
        help="Discharging port of freight order")
    state = fields.Selection([('draft', 'Draft'), ('submit', 'Submitted'),
                              ('confirm', 'Confirmed'),
                              ('invoice', 'Invoiced'), ('done', 'Done'),
                              ('cancel', 'Cancel')],
                             default='draft', tracking=True, copy=False,
                             help='Different states of freight order')
    clearance = fields.Boolean(copy=False, help='Checking the clearance')
    clearance_ids = fields.One2many('custom.clearance', 'freight_id',
                                    string='Custom Clearances',
                                    help='Custom clearances of the order')
    invoice_ids = fields.One2many('account.move', 'freight_order_id',
                                  string='Invoices', copy=False,
                                  help='Invoices created from the order')
    clearance_count = fields.Integer(compute='_compute_count',
                                     help='Number of custom clearances')
    invoice_count = fields.Integer(compute='_compute_count',
                                   help='The number of invoices created')
    total_order_price = fields.Float(string='Total',
                                     compute='_compute_total_order_price',
                                     help='The total order price')
    total_volume = fields.Float(compute='_compute_total_order_price',
                                help='The total used volume')
    total_weight = fields.Float(compute='_compute_total_order_price',
                                help='The total weight used')
    order_ids = fields.One2many('freight.order.line', 'order_id',
                                string='Freight Order Line',
                                help='The freight order lines of the order')
    route_ids = fields.One2many('freight.order.routes.line', 'freight_id',
                                help='The route of order')
    total_route_sale = fields.Float(string='Total Sale',
                                    compute="_compute_total_route_cost",
                                    help='The total cost of sale')
    service_ids = fields.One2many('freight.order.service', 'freight_id',
                                  help='Service of the order')
    total_service_sale = fields.Float(string='Service Total Sale',
                                      compute="_compute_total_service_cost",
                                      help='The total service cost of order')
    agent_id = fields.Many2one('res.partner', required=True, tracking=True,
                               help="Details of agent")
    expected_date = fields.Date(tracking=True,
                                help='The expected date of the order')
    track_ids = fields.One2many('freight.track', 'freight_id',
                                string='Tracking',
                                help='For tracking the freight orders')
    company_id = fields.Many2one('res.company', copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda self: self.env.company)

    @api.depends('order_ids.total_price', 'order_ids.volume',
                 'order_ids.weight')
    def _compute_total_order_price(self):
        """Computing the price of the order"""
        for rec in self:
            rec.total_order_price = sum(rec.order_ids.mapped('total_price'))
            rec.total_volume = sum(rec.order_ids.mapped('volume'))
            rec.total_weight = sum(rec.order_ids.mapped('weight'))

    @api.depends('route_ids.sale')
    def _compute_total_route_cost(self):
        """Computing the total cost of route operation"""
        for rec in self:
            rec.total_route_sale = sum(rec.route_ids.mapped('sale'))

    @api.depends('service_ids.total_sale')
    def _compute_total_service_cost(self):
        """Computing the total cost of services"""
        for rec in self:
            rec.total_service_sale = sum(rec.service_ids.mapped('total_sale'))

    @api.model_create_multi
    def create(self, vals_list):
        """Create Sequence for multiple records"""
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'freight.order.sequence') or 'New'
        return super().create(vals_list)

    @api.depends('clearance_ids', 'invoice_ids')
    def _compute_count(self):
        """Compute custom clearance and account move's count"""
        for rec in self:
            rec.clearance_count = len(rec.clearance_ids)
            rec.invoice_count = len(rec.invoice_ids)

    def _get_notify_partners(self):
        """Partners of the order that can be reached by email"""
        self.ensure_one()
        return (self.shipper_id | self.consignee_id | self.agent_id).filtered(
            'email')

    def _send_template_mail(self, xmlid):
        """Queue the mail template to the partners related to the order"""
        template = self.env.ref(xmlid, raise_if_not_found=False)
        for rec in self:
            partners = rec._get_notify_partners()
            if template and partners:
                template.send_mail(
                    rec.id, force_send=False,
                    email_values={'recipient_ids': [(4, pid) for pid in
                                                    partners.ids]})

    def _check_state(self, states):
        """Raise if any of the orders is not in one of the given states"""
        for rec in self:
            if rec.state not in states:
                raise ValidationError(self.env._(
                    "The order %(name)s can't be processed in its current "
                    "state.", name=rec.name))

    def action_create_custom_clearance(self):
        """Create custom clearance"""
        self.ensure_one()
        if self.clearance:
            raise ValidationError(self.env._(
                "A custom clearance has already been created for this "
                "freight order."))
        clearance = self.env['custom.clearance'].create({
            'freight_id': self.id,
            'date': self.order_date,
            'loading_port_id': self.loading_port_id.id,
            'discharging_port_id': self.discharging_port_id.id,
            'agent_id': self.agent_id.id,
        })
        self.clearance = True
        return {
            'name': self.env._('Custom Clearance'),
            'type': 'ir.actions.act_window',
            'views': [[False, 'form']],
            'target': 'current',
            'res_id': clearance.id,
            'res_model': 'custom.clearance',
        }

    def get_custom_clearance(self):
        """Get custom clearance"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Custom Clearance'),
            'view_mode': 'list,form',
            'res_model': 'custom.clearance',
            'domain': [('freight_id', '=', self.id)],
            'context': {'create': False},
        }

    def action_track_order(self):
        """Track the order"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Received/Delivered'),
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'freight.order.track',
            'context': {
                'default_freight_id': self.id,
            },
        }

    def _prepare_invoice_lines(self):
        """Prepare the invoice lines of the order. Lines without a billable
        quantity are skipped."""
        self.ensure_one()
        precision = self.env['decimal.precision'].precision_get(
            'Product Price')
        lines = []

        def add_line(name, qty, price, total, product=None):
            if float_is_zero(qty, precision_digits=precision):
                return
            if float_compare(total, qty * price,
                             precision_digits=precision):
                # The total was set manually: keep the invoice consistent
                price = total / qty
            vals = {'name': name, 'price_unit': price, 'quantity': qty}
            if product:
                vals['product_id'] = product.id
            lines.append(Command.create(vals))

        for line in self.order_ids:
            qty = line.weight if line.billing_type == 'weight' else (
                line.volume if line.billing_type == 'volume' else 0.0)
            add_line(line.product_id.name or self.env._('Freight Cargo'),
                     qty, line.price, line.total_price, line.product_id)
        for route in self.route_ids:
            add_line(route.routes_id.name, 1.0, route.sale, route.sale)
        for service in self.service_ids:
            add_line(service.service_id.name, service.qty, service.sale,
                     service.total_sale)
        return lines

    def action_create_invoice(self):
        """Create invoice"""
        self.ensure_one()
        self._check_state(('confirm',))
        if self.invoice_ids.filtered(lambda m: m.state != 'cancel'):
            raise ValidationError(self.env._(
                "An invoice has already been created for this freight "
                "order."))
        lines = self._prepare_invoice_lines()
        if not lines:
            raise ValidationError(self.env._(
                "There is nothing to invoice: add order lines with a "
                "billing type and quantity, routes or services."))
        inv = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.shipper_id.id,
            'invoice_user_id': self.env.user.id,
            'invoice_origin': self.name,
            'ref': self.name,
            'freight_order_id': self.id,
            'invoice_line_ids': lines,
        })
        self.state = 'invoice'
        return {
            'name': self.env._('Customer Invoice'),
            'type': 'ir.actions.act_window',
            'views': [[False, 'form']],
            'target': 'current',
            'res_id': inv.id,
            'res_model': 'account.move',
        }

    def action_cancel(self):
        """Cancel the order and release reserved containers"""
        self._check_state(('draft', 'submit', 'confirm', 'invoice'))
        for rec in self:
            if rec.invoice_ids.filtered(lambda m: m.state != 'cancel'):
                raise ValidationError(self.env._(
                    "Cancel the invoices of the order %(name)s before "
                    "cancelling it.", name=rec.name))
            rec.state = 'cancel'
            rec.order_ids.container_id.filtered(
                lambda c: c.state == 'reserve').sudo().state = 'available'

    def get_invoice(self):
        """View the invoice"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Invoice'),
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [('freight_order_id', '=', self.id)],
            'context': {'create': False},
        }

    def action_submit(self):
        """Submitting order and sending email notification"""
        self._check_state(('draft',))
        for rec in self:
            rec.state = 'submit'
            rec._send_template_mail(
                'freight_management_system.'
                'mail_template_freight_order_submitted')
            rec.message_post(body=self.env._(
                "Freight Order %s has been submitted.", rec.name))

    def action_confirm(self):
        """Confirm order"""
        self._check_state(('submit',))
        for rec in self:
            if not rec.clearance_ids:
                raise ValidationError(self.env._(
                    "Create a custom clearance for %s", rec.name))
            pending = rec.clearance_ids.filtered(
                lambda c: c.state == 'draft')
            if pending:
                raise ValidationError(self.env._(
                    "The custom clearance '%s' is not confirmed.",
                    pending[0].name))
        for rec in self:
            rec.state = 'confirm'
            rec.order_ids.container_id.sudo().state = 'reserve'
            rec._send_template_mail(
                'freight_management_system.'
                'mail_template_freight_order_confirmed')
            rec.message_post(body=self.env._(
                "Freight Order %s has been confirmed.", rec.name))

    def action_done(self):
        """Mark order as done"""
        self._check_state(('confirm', 'invoice'))
        for rec in self:
            rec.state = 'done'
            rec._send_template_mail(
                'freight_management_system.mail_template_freight_order_done')
            rec.message_post(body=self.env._(
                "Freight Order %s has been marked as Completed.", rec.name))
            rec.order_ids.container_id.sudo().state = 'available'


class FreightOrderLine(models.Model):
    """Freight order lines are defined"""
    _name = 'freight.order.line'
    _description = 'Freight Order Line'

    order_id = fields.Many2one('freight.order', string="Freight Order",
                               ondelete='cascade',
                               help="Reference from freight order")
    container_id = fields.Many2one(
        'freight.container', domain="[('state', '=', 'available')]",
        help='The freight container')
    product_id = fields.Many2one('product.product', string='Goods',
                                 help='The Freight Products')
    billing_type = fields.Selection(
        [('weight', 'Weight'), ('volume', 'Volume')],
        string="Billing On",
                                    help='Select the billing type for '
                                         'calculating the total amount')
    pricing_id = fields.Many2one('freight.price', help='The pricing of order')
    price = fields.Float(string='Unit Price', compute='_compute_price',
                         store=True, readonly=False,
                         help='Unit price of the selected goods')
    total_price = fields.Float(compute='_compute_total_price',
                               store=True, readonly=False,
                               help='This will be the total price')
    volume = fields.Float(help='Volume of the goods')
    weight = fields.Float(help='Weight of the goods')
    company_id = fields.Many2one('res.company', copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda self: self.env.company)

    @api.constrains('weight', 'container_id', 'billing_type')
    def _check_weight(self):
        """Checking the weight of containers"""
        for rec in self:
            if rec.container_id and rec.billing_type:
                if rec.billing_type == 'weight':
                    if rec.container_id.weight < rec.weight:
                        raise ValidationError(
                            self.env._(
                                'The weight must be less than or '
                                'equal to %(weight)s',
                                weight=rec.container_id.weight,
                            ),
                        )

    @api.constrains('volume', 'container_id', 'billing_type')
    def _check_volume(self):
        """Checking the volume of containers"""
        for rec in self:
            if rec.container_id and rec.billing_type:
                if rec.billing_type == 'volume':
                    if rec.container_id.volume < rec.volume:
                        raise ValidationError(
                            self.env._(
                                'The volume must be less than or '
                                'equal to %(volume)s',
                                volume=rec.container_id.volume,
                            ),
                        )

    @api.depends('pricing_id', 'billing_type')
    def _compute_price(self):
        """Calculate the price based on pricing and billing type"""
        for rec in self:
            if rec.billing_type == 'weight' and rec.pricing_id:
                rec.price = rec.pricing_id.weight
            elif rec.billing_type == 'volume' and rec.pricing_id:
                rec.price = rec.pricing_id.volume
            elif not rec.price:
                rec.price = 0.0

    @api.onchange('billing_type')
    def _onchange_billing_type(self):
        """Reset dimension when changing billing type"""
        if self.billing_type == 'weight':
            self.volume = 0.00
        elif self.billing_type == 'volume':
            self.weight = 0.00

    @api.depends('billing_type', 'volume', 'weight', 'price')
    def _compute_total_price(self):
        """Calculate sub total price"""
        for rec in self:
            if rec.billing_type == 'weight':
                rec.total_price = rec.weight * rec.price
            elif rec.billing_type == 'volume':
                rec.total_price = rec.volume * rec.price
            else:
                rec.total_price = 0.0


class FreightOrderRoutesLine(models.Model):
    """Defining the routes for the shipping, also we can add the operations for
    the routes."""
    _name = 'freight.order.routes.line'
    _description = 'Freight Order Routes Lines'

    freight_id = fields.Many2one('freight.order', string='Freight Order',
                                 ondelete='cascade',
                                 help='Relation from freight order')
    routes_id = fields.Many2one('freight.routes', required=True,
                                help='Select route of freight')
    source_loc_id = fields.Many2one('freight.port', string='Source Location',
                                    help='Select the source port')
    destination_loc_id = fields.Many2one('freight.port',
                                         string='Destination Location',
                                         help='Select the destination port')
    transport_type = fields.Selection([('land', 'Land'), ('air', 'Air'),
                                       ('water', 'Water')], string="Transport",
                                      required=True,
                                      help='Select the transporting medium')
    sale = fields.Float(compute='_compute_sale',
                        store=True, readonly=False,
                        help="Set the price for route operation")
    company_id = fields.Many2one('res.company', copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda self: self.env.company)

    @api.depends('routes_id', 'transport_type')
    def _compute_sale(self):
        """Calculate the price of route operation"""
        for rec in self:
            if rec.routes_id and rec.transport_type:
                if rec.transport_type == 'land':
                    rec.sale = rec.routes_id.land_sale
                elif rec.transport_type == 'air':
                    rec.sale = rec.routes_id.air_sale
                elif rec.transport_type == 'water':
                    rec.sale = rec.routes_id.water_sale
            elif not rec.sale:
                rec.sale = 0.0


class FreightOrderServiceLine(models.Model):
    """Services in freight orders"""
    _name = 'freight.order.service'
    _description = 'Freight Order Service'

    freight_id = fields.Many2one('freight.order', string='Freight Order',
                                 ondelete='cascade',
                                 help='Relation from freight order')
    service_id = fields.Many2one('freight.service', required=True,
                                 help='Select the service')
    partner_id = fields.Many2one('res.partner', string="Vendor",
                                 help='Select the partner for the service')
    qty = fields.Float(string='Quantity', help='Quantity required')
    cost = fields.Float(help='The cost price of the service')
    sale = fields.Float(compute='_compute_sale',
                        store=True, readonly=False,
                        help='Sale price of the service')
    total_sale = fields.Float(compute='_compute_total_sale',
                              store=True, readonly=False,
                              help='The total sale price')
    company_id = fields.Many2one('res.company', copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda self: self.env.company)

    @api.depends('service_id', 'partner_id')
    def _compute_sale(self):
        """Calculate the price of services"""
        for rec in self:
            if rec.service_id:
                if rec.partner_id and rec.service_id.line_ids:
                    partner_service = rec.service_id.line_ids.filtered(
                        lambda s: s.partner_id == rec.partner_id)
                    rec.sale = (
                        partner_service[0].sale
                        if partner_service
                        else rec.service_id.sale_price
                    )
                else:
                    rec.sale = rec.service_id.sale_price
            elif not rec.sale:
                rec.sale = 0.0

    @api.depends('qty', 'sale')
    def _compute_total_sale(self):
        """Calculate the subtotal of service"""
        for rec in self:
            rec.total_sale = rec.qty * rec.sale


class Tracking(models.Model):
    """Tracking the freight order"""
    _name = 'freight.track'
    _description = 'Freight Track'

    source_loc_id = fields.Many2one('freight.port', string='Source Location',
                                    help='Select the source location of port')
    destination_loc_id = fields.Many2one(
        'freight.port', string='Destination Location',
        help='Destination location of the port')
    transport_type = fields.Selection([('land', 'Land'), ('air', 'Air'),
                                       ('water', 'Water')], string='Transport',
                                      help='Transporting medium of the order')
    freight_id = fields.Many2one('freight.order', string='Freight Order',
                                 ondelete='cascade',
                                 help='Reference from freight order')
    date = fields.Date(help='Select the date')
    type = fields.Selection([('received', 'Received'),
                             ('delivered', 'Delivered')],
                            string='Received/Delivered',
                            help='Status of the order')
    company_id = fields.Many2one('res.company', copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda self: self.env.company)
