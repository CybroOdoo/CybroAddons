# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Risvana AR (odoo@cybrosys.com)
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
from odoo.exceptions import UserError, ValidationError


class VenueBooking(models.Model):
    """Model for managing the Venue Booking"""
    _name = 'venue.booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Venue Reservation'

    name = fields.Char(string="Name", help="Name of the venue type")
    ref = fields.Char(string='Ref', readonly=True,
                      help="Name of the venue that created as sequencing")
    venue_id = fields.Many2one('venue', string='Venue',
                               help="Venue for the Event", required=True)
    venue_type_id = fields.Many2one('venue.type',
                                    'Venue Type',
                                    related='venue_id.venue_type_id',
                                    readonly=True,
                                    help='Used to choose the type of the particular venue')
    image = fields.Binary("Image", attachment=True,
                          related='venue_type_id.image',
                          help="This field holds the image used as "
                               "image for the event, limited to 1080x720px.")
    partner_id = fields.Many2one('res.partner', string="Customer",
                                 required=True,
                                 help='Used to Choose the Booking Person')
    date = fields.Date(string="Date", default=fields.Date.today, required=True,
                       help='Date field for booking the Venue')
    currency_id = fields.Many2one('res.currency', readonly=True,
                                  string='Currency',
                                  default=lambda self:
                                  self.env.user.company_id.currency_id,
                                  help='Currency field for booking Venue')
    start_date = fields.Datetime(string="Start date",
                                 default=lambda self: fields.datetime.now(),
                                 required=True,
                                 help='Venue Booking Start Date')
    end_date = fields.Datetime(string="End date", required=True,
                               help='Venue Booking End Date')
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirmed'),
                              ('invoice', 'Invoiced'),
                              ('close', 'Close'), ('cancel', 'Canceled')],
                             string="State", default="draft",
                             help="State of venue booking")
    booking_type = fields.Selection([('day', 'Day'),
                                     ('hour', 'Hours')], string='Booking Type',
                                    default='day',
                                    help='The selection field for Booking Type')
    venue_booking_line_ids = fields.One2many('venue.booking.line',
                                             'venue_booking_id',
                                             string="Venues",
                                             help='Booking Line for the given venue')
    note = fields.Text(string='Terms and conditions',
                       help='The note field for Venue Booking')
    pending_invoice = fields.Boolean(string="Invoice Pending",
                                     compute='_compute_pending_invoice',
                                     help='Find out is there any pending invoice')
    total = fields.Monetary(string="Total Amount", store=True,
                            compute='_compute_total_amount',
                            help='Total amount for the Venue Booking')
    booking_charge_per_day = fields.Float(string="Booking Charge Per Day",
                                          related='venue_id.venue_charge_day',
                                          help='Field for adding Booking Charge Per Day')
    booking_charge_per_hour = fields.Float(string="Booking Charge Per Hour",
                                           related='venue_id.venue_charge_hour',
                                           help='Field for adding Booking Charge Per hour')
    booking_charge = fields.Float(string="Venue Amenities Charge",
                                  compute='_compute_booking_charge',
                                  help='Compute the total Booking cost includes the amenities')
    days_difference = fields.Integer(string='Days Difference',
                                     compute='_compute_days_difference',
                                     help='Number of Days to Booking the venue')
    invoice_count = fields.Integer(string="Invoice Count",
                                   compute='_compute_invoice_count',
                                   help='Total invoice count')
    is_additional_charge = fields.Boolean(string="Add Extra Charge?",
                                          help='Add additional charge for the booking')
    amenity_line_ids = fields.One2many('venue.booking.line',
                                       'venue_booking_id',
                                       string="Included Amenities",
                                       help='Booking Line for the given venue')

    @api.constrains('venue_booking_line_ids')
    def _check_venue_booking_line_ids(self):
        """Check if the venue bookings line contains already taken amenities"""
        amenities_list = []
        name_list = []
        if self.venue_id.venue_line_ids:
            amenities = self.venue_id.venue_line_ids.mapped('amenities_id')
            for line in self.venue_booking_line_ids:
                if line.amenity_id in amenities:
                    amenities_list.append(line.amenity_id)
                    name_list.append(line.amenity_id.name)
        if amenities_list:
            names = ', '.join(name_list)
            raise ValidationError(
                _("Amenities %s are already Include in Your Venue Booking %s"
                  % (str(names), str(self.venue_id.name))))

    @api.model
    def create(self, values):
        """Create method for sequencing and checking dates while Booking the Venues"""
        start_date = values['start_date']
        end_date = values['end_date']
        date = values['date']
        partner_name = self.env['res.partner'].browse(
            values['partner_id']).name
        if start_date >= end_date:
            raise UserError(_('Start date must be less than End date'))
        values['name'] = '%s- %s' % (partner_name, date)
        values['ref'] = self.env['ir.sequence'].next_by_code(
            'venue.booking.sequence')
        res = super().create(values)
        return res

    @api.onchange('start_date', 'end_date')
    def _onchange_booking_dates(self):
        """Checking dates while Booking the Venues based on the changes of the Dates"""
        if self.venue_id:
            booking = self.env['venue.booking'].search(
                [('start_date', '<', self.end_date),
                 ('end_date', '>', self.start_date),
                 ('venue_id', '=', self.venue_id.id)])
            if booking:
                raise ValidationError(
                    "Venue is not available for the selected time range.")

    @api.depends('start_date', 'end_date')
    def _compute_days_difference(self):
        """Compute the difference between start and end dates for Calculating the days"""
        for record in self:
            if record.start_date and record.end_date:
                delta = record.end_date - record.start_date
                record.days_difference = delta.days
            else:
                record.days_difference = 0

    @api.depends('booking_charge', 'venue_id')
    def _compute_booking_charge(self):
        """Compute booking charge for the given venue with the Amenities"""
        for rec in self:
            rec.booking_charge = rec.venue_id.price_subtotal if rec.venue_id else 0.0

    @api.depends('venue_booking_line_ids', 'venue_booking_line_ids.state')
    def _compute_pending_invoice(self):
        """Compute function for finding the pending Invoices"""
        for pending in self:
            pending.pending_invoice = any(
                not line.is_invoiced and line.state == "done" for line in
                pending.venue_booking_line_ids)

    @api.depends('venue_booking_line_ids.sub_total', 'booking_charge_per_hour',
                 'booking_charge_per_day')
    def _compute_total_amount(self):
        """Compute total amount of bookings with the Charge of the Particular venue"""
        total = sum(item.sub_total for item in self.venue_booking_line_ids)
        for rec in self:
            if rec.booking_type == 'day':
                total += (rec.booking_charge_per_day * rec.days_difference)
                if rec.venue_id.additional_charge_day != 0.0:
                    total += rec.venue_id.additional_charge_day
            elif rec.booking_type == 'hour':
                total += (rec.booking_charge_per_hour * rec.days_difference)
                if rec.venue_id.additional_charge_hour != 0.0:
                    total += rec.venue_id.additional_charge_hour
            rec.total = total + rec.booking_charge

    @api.constrains('start_date', 'end_date', 'venue_id')
    def check_date_overlap(self):
        """Check the date overlap between the start and end dates"""
        for booking in self:
            overlapping_bookings = self.env['venue.booking'].search([
                ('venue_id', '=', booking.venue_id.id),
                ('start_date', '<', booking.end_date),
                ('end_date', '>', booking.start_date),
                ('id', '!=', booking.id),  # Exclude the current record itself
            ])
            if overlapping_bookings:
                raise ValidationError(
                    "Booking dates overlap with existing bookings.")

    def action_booking_confirm(self):
        """Button action to confirm"""
        for booking in self:
            bookings = self.env['venue.booking'].search([
                ('venue_id', '=', booking.venue_id.id),
                ('start_date', '<', booking.end_date),
                ('end_date', '>', booking.start_date),
                ('id', '!=', booking.id),  # Exclude the current record itself
            ])
            if bookings:
                raise ValidationError(
                    "Booking dates overlap with existing bookings.")
            else:
                self.state = "confirm"

    def action_reset_to_draft(self):
        """Button action to reset"""
        self.state = "draft"

    def action_send_confirmation_mail(self):
        """Button action to send confirmation mail"""
        template = self.env.ref(
            'venue_booking_management.mail_template_notify_venue_booking').sudo()
        template.send_mail(self._origin.id, force_send=True,
                           email_values={
                               'email_to': self.partner_id.email})

    def action_booking_invoice_create(self):
        """Button action to create related invoice"""
        invoice_id = self.env['account.move'].search(
            [('invoice_origin', '=', self.ref), ('state', '=', 'draft')])
        amenity_lists = []

        def add_charge(name, price_unit, quantity=1):
            amenity_lists.append({
                'name': name,
                'price_unit': price_unit,
                'quantity': quantity,
            })

        if self.booking_type == 'day':
            total = self.booking_charge_per_day + self.venue_id.additional_charge_day
        elif self.booking_type == 'hour':
            total = self.booking_charge_per_hour + self.venue_id.additional_charge_hour
        else:
            total = 0
        add_charge('Amenities charge', self.booking_charge)
        add_charge('Booking Charges', total)
        for rec in self.venue_booking_line_ids:
            add_charge(rec.amenity_id.name, rec.amount, rec.quantity)
        if self.is_additional_charge:
            is_extra = self.env['ir.config_parameter'].sudo(). \
                get_param('venue_booking_management.is_extra')
            if is_extra:
                amount = self.env['ir.config_parameter'].sudo(). \
                    get_param('venue_booking_management.extra_amount')
                amenity_lists.append({
                    'name': 'Extra charges',
                    'price_unit': amount,
                    'quantity': '1',
                })
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_origin': self.ref,
            'invoice_line_ids': [(0, 0, line) for line in amenity_lists],
        }
        if not invoice_id:
            invoice = self.env['account.move'].create([invoice_vals])
            self.state = "invoice"
            return {
                'name': 'Invoice',
                'view_mode': 'form',
                'res_id': invoice.id,
                'res_model': 'account.move',
                'type': 'ir.actions.act_window',
                'target': 'current',
            }
        else:
            # Unlink existing lines
            invoice_id.invoice_line_ids.unlink()
            invoice_id.write(
                {'invoice_line_ids': [(0, 0, line) for line in amenity_lists]})
            self.state = "invoice"
            return {
                'name': 'Invoice',
                'view_mode': 'form',
                'res_id': invoice_id.id,
                'res_model': 'account.move',
                'type': 'ir.actions.act_window',
                'target': 'current',
            }

    def action_view_invoice(self):
        """Smart button to view the Corresponding Invoices for the Venue Booking"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'target': 'current',
            'domain': [('invoice_origin', '=', self.ref)],
            'context': {"create": False},
        }

    def _compute_invoice_count(self):
        """Function to count invoice"""
        for record in self:
            record.invoice_count = self.env['account.move']. \
                search_count([('invoice_origin', '=', self.ref)])

    def action_booking_cancel(self):
        """Button action to move the cancel state"""
        self.state = "cancel"

    def action_booking_close(self):
        """Button action to close the records"""
        if any(not line.is_invoiced for line in self.venue_booking_line_ids):
            raise ValidationError(_('You can close The Booking only when all '
                                    'Procedure is Done and Invoiced'))
        else:
            self.state = "close"

    @api.model
    def get_total_booking(self):
        """Function to get total booking, distance and invoice amount details"""
        total_booking = self.env['venue.booking'].search_count([])
        booking_ids = self.env['venue.booking'].search(
            [('state', 'not in', ['draft', 'cancel', 'close'])])
        invoice_ids = self.env['venue.booking']. \
            search([('state', '=', 'invoice')]).mapped('total')
        venue_ids = self.env['venue'].search_count([])
        return {'total_booking': total_booking,
                'total_invoice': sum(invoice_ids),
                'total_amount': sum(booking_ids.mapped('total')),
                'total_venue': venue_ids}

    @api.model
    def get_top_venue(self):
        """Function to return top venue and customer details query to js"""
        self.env.cr.execute('''select fv.name,count(tb.name) from venue_booking as tb
                            inner join venue as fv on fv.id = tb.venue_id
                            group by fv.name order by count(tb.name) desc limit 10''')
        venue = self.env.cr.dictfetchall()
        self.env.cr.execute('''select pr.name,count(tb.name) from venue_booking as tb
                                   inner join res_partner as pr on pr.id = tb.partner_id
                                   group by pr.name order by count(tb.name) desc limit 10''')
        customer = self.env.cr.dictfetchall()
        self.env.cr.execute('''select tb.ref, pr.name, tb.date from 
                                    venue_booking as tb
                                    inner join res_partner as pr on pr.id = tb.partner_id
                                    where tb.date >= '%s' and tb.state = 'invoice'
                                    order by tb.date''' % fields.date.today())
        upcoming = self.env.cr.dictfetchall()
        return {'venue': venue, 'customer': customer, 'upcoming': upcoming}

    @api.model
    def get_booking_analysis(self):
        """Function to return customer details to js for graph view"""
        self.env.cr.execute('''select pr.name,sum(tb.total) from venue_booking as tb
                                    inner join res_partner as pr on pr.id = tb.partner_id
                                    group by pr.name order by sum(tb.total)''')
        booking = self.env.cr.dictfetchall()
        count = []
        customer = []
        for record in booking:
            customer.append(record.get('name'))
            count.append(record.get('sum'))
        value = {'name': customer, 'count': count}
        return value

    @api.model
    def get_venue_analysis(self):
        """Function to return truck details to js for graph view"""
        self.env.cr.execute('''select fv.name,sum(tb.total) from venue_booking as tb
                            inner join venue as fv on fv.id = tb.venue_id
                            group by fv.name order by sum(tb.total)''')
        booking = self.env.cr.dictfetchall()
        count = []
        customer = []
        for record in booking:
            customer.append(record.get('name'))
            count.append(record.get('sum'))
        return {'name': customer, 'count': count}

    @api.model
    def get_select_filter(self, option):
        """Function to filter data on the bases of the year"""
        if option == 'year':
            create_date = '''create_date between (now() - interval '1 year') and now()'''
        elif option == 'month':
            create_date = '''create_date between (now() - interval '1 months') and now()'''
        elif option == 'week':
            create_date = '''create_date between (now() - interval '7 day') and now()'''
        elif option == 'day':
            create_date = '''create_date between (now() - interval '1 day') and now()'''

        self.env.cr.execute('''select count(*) from venue_booking 
                                    where %s''' % create_date)
        booking = self.env.cr.dictfetchall()
        self.env.cr.execute('''select sum(total) from venue_booking 
                                    where %s''' % create_date)
        amount = self.env.cr.dictfetchall()
        self.env.cr.execute('''select sum(total) from venue_booking
                                        where state = 'invoice' and %s''' % create_date)
        invoice = self.env.cr.dictfetchall()
        self.env.cr.execute('''select fv.name,count(name) from venue_booking as tb
                                    inner join venue as fv on fv.id = tb.venue_id
                                     where tb.%s
                                    group by name
                                    order by count desc
                                    limit 10''' % create_date)
        venue = self.env.cr.dictfetchall()
        self.env.cr.execute('''select pr.name,count(name) from venue_booking as tb
                                           inner join res_partner as pr on pr.id = tb.partner_id
                                            where tb.%s group by name
                                           order by count desc limit 10''' % create_date)
        customer = self.env.cr.dictfetchall()
        self.env.cr.execute('''select pr.name,sum(tb.total) from venue_booking as tb
                                     inner join res_partner as pr on pr.id = tb.partner_id
                                     where tb.%s group by name''' % create_date)
        cust_invoice = self.env.cr.dictfetchall()
        cust_invoice_name = []
        cust_invoice_sum = []
        for record in cust_invoice:
            cust_invoice_name.append(record.get('name'))
            cust_invoice_sum.append(record.get('sum'))
        self.env.cr.execute('''select fv.name,sum(tb.total) from venue_booking as tb
                                    inner join venue as fv on fv.id = tb.venue_id
                                    where tb.%s group by name''' % create_date)
        truck_invoice = self.env.cr.dictfetchall()
        truck_invoice_name = []
        truck_invoice_count = []
        for record in truck_invoice:
            truck_invoice_name.append(record.get('name'))
            truck_invoice_count.append(record.get('sum'))

        return {'booking': booking, 'amount': amount,
                'invoice': invoice, 'venue': venue, 'customer': customer,
                'cust_invoice_name': cust_invoice_name, 'cust_invoice_sum':
                    cust_invoice_sum, 'truck_invoice_name': truck_invoice_name,
                'truck_invoice_count': truck_invoice_count,
                }


class VenueBookingLine(models.Model):
    """Model to manage the Venue Booking lines of the Venue Reservation"""
    _name = 'venue.booking.line'
    _description = "Venue Booking"

    venue_booking_id = fields.Many2one('venue.booking',
                                       string="Venue Booking",
                                       help='The relation added for the venue Booking ')
    state = fields.Selection([('done', 'Done'), ('pending', 'Pending')],
                             string="State", default="pending",
                             readonly=True,
                             help="The state of the venue Booking line")
    currency_id = fields.Many2one('res.currency', readonly=True,
                                  default=lambda self:
                                  self.env.user.company_id.currency_id,
                                  string="Currency",
                                  help="The currency of the booking line")
    is_invoiced = fields.Boolean(string="Invoiced", readonly=True,
                                 help="The boolean value used for finding the "
                                      "venue booking is invoiced or not")
    venue_type_id = fields.Many2one('venue.type',
                                    string="Related Venue Type",
                                    related='venue_booking_id.venue_type_id',
                                    help="The venue type of the booking line")
    amenity_id = fields.Many2one('amenities', string='Amenities',
                                 help='The relational field for the booking '
                                      'line with the amenities model')
    quantity = fields.Float(string="Quantity", default=1,
                            help="Quantity of the Amenities")
    amount = fields.Float(string="Amount", help="Amount of the Amenities",
                          related='amenity_id.amount')
    sub_total = fields.Float(string="Sub Total",
                             compute="_compute_extra_sub_total",
                             readonly=True, help="Sub Total of the Values")

    @api.depends('quantity', 'amount')
    def _compute_extra_sub_total(self):
        """Compute function for the Amenities"""
        for booking in self:
            booking.sub_total = booking.quantity * booking.amount
