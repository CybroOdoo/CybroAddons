# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from math import asin, cos, sin, radians, sqrt
from geopy import Nominatim
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TruckBooking(models.Model):
    """Class to add truck_booking menu to view all truck_booking"""
    _name = "truck.booking"
    _description = "Truck Booking"
    _inherit = 'mail.thread', 'mail.activity.mixin'
    _rec_name = 'reference_no'

    reference_no = fields.Char(string='Order Reference', readonly=True,
                               default=lambda self: _('New'), copy=False,
                               help='Order reference number')
    partner_id = fields.Many2one('res.partner', string='Customer',
                                 required=True, help='Customer Name')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.user.company_id.id,
        help='Select the company to which this record belongs.'
    )
    from_location = fields.Char(string='Pickup City', required=True,
                                help='Goods source location')
    to_location = fields.Char(string='Drop City', required=True,
                              help='Goods destination location')
    distance = fields.Float(string='Distance', compute='_compute_distance',
                            store=True, help='Total distance to travel')
    truck_id = fields.Many2one('fleet.vehicle.model',
                               string='Truck Type',
                               domain=[('vehicle_type', '=', 'truck')],
                               required=True, help='Select the truck type')
    goods_type_id = fields.Many2one('goods.type',
                                    string='Goods Type',
                                    help='Select goods type', required=True)
    weight = fields.Integer(string='Weight', help='Total weight of goods')
    amount = fields.Float(string='Amount', compute='_compute_amount',
                          store=True,
                          help='Total amount is the distance travelled by the'
                               ' truck')
    date = fields.Date(string='Date', help='Delivery date')
    unit = fields.Selection(selection=[('kg', 'KG'), ('tons', 'Tons')],
                            string='Unit', default='kg', help='Select unit')
    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('confirm', 'Confirm'),
                                        ('invoice', 'Invoiced')],
                             string='State', default="draft",
                             help="Booking State", index=True, tracking=True)
    invoice_count = fields.Integer(string="Invoice Count",
                                   compute='_compute_invoice_count',
                                   help='Total invoice count')
    invoiced_amount = fields.Float(string='Invoiced amount',
                                   compute='_compute_invoiced_amount',
                                   help='Total invoiced amount')
    hide_invoice = fields.Boolean(string='Hide Invoice',
                                  help="To hide create invoice button",
                                  default=False)

    @api.constrains('distance')
    def _check_distance_limit(self):
        """Check the distance against the configured maximum distance limit."""
        is_distance_limited = self.env['ir.config_parameter'].sudo().get_param(
            'packers_and_movers_management.is_distance_limited', default=False)
        max_distance = float(self.env['ir.config_parameter'].sudo().get_param(
            'packers_and_movers_management.max_distance', default=0.0))
        for record in self:
            if is_distance_limited and record.distance > max_distance:
                raise ValidationError(
                    _("The distance of %s KM exceeds the maximum allowed "
                      "distance of %s KM. Please reduce the distance or "
                      "update the settings.") % (
                        record.distance, max_distance))

    def _compute_invoice_count(self):
        """Function to count invoice"""
        for record in self:
            record.invoice_count = self.env['account.move']. \
                search_count([('invoice_origin', '=', self.reference_no)])

    def _compute_invoiced_amount(self):
        """Function to add invoiced amount"""
        for record in self:
            invoices = record.env['account.move'].search([
                ('invoice_origin', '=', record.reference_no),
                ('state', '!=', 'cancel')])
            record.invoiced_amount = sum(
                invoices.mapped('amount_untaxed_signed'))
            record.hide_invoice = sum(
                invoices.mapped('amount_untaxed_signed')) == record.amount

    @api.depends('from_location', 'to_location')
    def _compute_distance(self):
        """Function to calculate distance between from and to location"""
        for location in self:
            locator = Nominatim(user_agent="my_distance_app")
            from_location = locator.geocode(location.from_location)
            to_location = locator.geocode(location.to_location)
            if from_location is None or to_location is None:
                raise ValidationError(_("Please enter valid city."))
            else:
                from_lat = radians(from_location.latitude)
                from_long = radians(from_location.longitude)
                to_lat = radians(to_location.latitude)
                to_long = radians(to_location.longitude)
                dist_long = to_long - from_long
                dist_lat = to_lat - from_lat
                comp = sin(dist_lat / 2) ** 2 + cos(from_lat) * cos(
                    to_lat) * sin(dist_long / 2) ** 2
                location.distance = int(2 * asin(sqrt(comp)) * 6371)

    @api.depends('distance')
    def _compute_amount(self):
        """Function to calculate amount for booking"""
        for record in self:
            amount = record.env['ir.config_parameter'].sudo(). \
                get_param('packers_and_movers_management.distance_amount')
            total = float(amount) * record.distance
            is_extra = record.env['ir.config_parameter'].sudo(). \
                get_param('packers_and_movers_management.is_extra')
            if is_extra:
                extra_amount = record.env['ir.config_parameter'].sudo(). \
                    get_param('packers_and_movers_management.extra_amount')
                total *= float(extra_amount)
            record.amount = total

    @api.onchange('date')
    def _onchange_date(self):
        """Adding validations for the date """
        if self.date and self.date < fields.Datetime.today().date():
            raise ValidationError(
                "Selected date cannot be before today's date.")

    @api.model_create_multi
    def create(self, vals_list):
        """Function to create a sequence"""
        for vals in vals_list:
            if vals.get('reference_no', _('New')) == _('New'):
                vals['reference_no'] = self.env['ir.sequence'].next_by_code(
                    'truck.booking') or _('New')
        return super(TruckBooking, self).create(vals_list)

    def action_confirm(self):
        """Function to change state to confirm"""
        self.write({'state': 'confirm'})

    def action_create_invoice(self):
        """Function to create invoice for the booking"""
        invoice_id = self.env['account.move'].search(
            [('invoice_origin', '=', self.reference_no),
             ('state', '=', 'draft')])
        if not invoice_id:
            invoice = self.env['account.move'].create([{
                'move_type': 'out_invoice',
                'partner_id': self.partner_id.id,
                'invoice_origin': self.reference_no,
                'invoice_line_ids': [fields.Command.create({
                    'name': "{} to {}".format(self.from_location,
                                              self.to_location),
                    'quantity': 1,
                    'price_unit': self.amount - self.invoiced_amount,
                    'price_subtotal': self.amount})]}])
            return {
                'name': 'Invoice',
                'view_mode': 'form',
                'res_id': invoice.id,
                'res_model': 'account.move',
                'type': 'ir.actions.act_window',
                'target': 'current',
            }

    def action_view_invoice(self):
        """Smart button to view the Corresponding Invoices for the
         truck_booking"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'target': 'current',
            'domain': [('invoice_origin', '=', self.reference_no)],
            'context': {"create": False},
        }

    @api.model
    def get_total_booking(self):
        """Function to get total booking, distance and invoice
         amount details"""
        total_booking = self.env['truck.booking'].search_count([])
        booking_ids = self.env['truck.booking'].search([])
        invoice_ids = self.env['truck.booking']. \
            search([('state', '=', 'invoice')]).mapped('amount')
        return {'total_booking': total_booking,
                'total_distance_count': sum(booking_ids.mapped('distance')),
                'total_invoice': sum(invoice_ids),
                'total_amount': sum(booking_ids.mapped('amount'))}

    @api.model
    def get_top_truck(self):
        """Return top trucks, top customers, and upcoming bookings."""
        cr = self.env.cr
        # Top trucks
        cr.execute(
            """
            SELECT fv.name, count(name)
            FROM truck_booking AS tb
            INNER JOIN fleet_vehicle_model AS fv ON fv.id = tb.truck_id
            GROUP BY name
            ORDER BY count DESC
            LIMIT 10
            """
        )
        truck = cr.dictfetchall()
        # Top customers
        cr.execute(
            """
            SELECT pr.name, count(pr.id) AS count
            FROM truck_booking AS tb
            INNER JOIN res_partner AS pr ON pr.id = tb.partner_id
            GROUP BY pr.id, pr.name
            ORDER BY count DESC
            LIMIT 10
            """
        )
        customer = cr.dictfetchall()
        # Upcoming invoices
        cr.execute(
            """
            SELECT tb.reference_no, pr.name, tb.date
            FROM truck_booking AS tb
            INNER JOIN res_partner AS pr ON pr.id = tb.partner_id
            WHERE tb.date >= %s AND tb.state = 'invoice'
            ORDER BY tb.date
            """,
            (fields.Date.today(),)
        )
        upcoming = cr.dictfetchall()
        return {
            'truck': truck,
            'customer': customer,
            'upcoming': upcoming
        }

    @api.model
    def get_booking_analysis(self):
        """Return customer booking amounts for graph view."""
        cr = self.env.cr
        cr.execute(
            """
            SELECT pr.name, sum(tb.amount)
            FROM truck_booking AS tb
            INNER JOIN res_partner AS pr ON pr.id = tb.partner_id
            GROUP BY pr.id, pr.name
            """
        )
        booking = cr.dictfetchall()
        customer = [rec.get('name') for rec in booking]
        count = [rec.get('sum') for rec in booking]
        return {'name': customer, 'count': count}

    @api.model
    def get_truck_analysis(self):
        """Function to return truck details to js for graph view"""
        self.env.cr.execute('''select fv.name,sum(tb.amount) from truck_booking
        as tb inner join fleet_vehicle_model as fv on fv.id = tb.truck_id
        group by name''')
        booking = self.env.cr.dictfetchall()
        count = []
        customer = []
        for record in booking:
            customer.append(record.get('name'))
            count.append(record.get('sum'))
        return {'name': customer, 'count': count}

    @api.model
    def get_distance(self):
        """Return total distance grouped by customer and truck."""
        cr = self.env.cr
        cr.execute(
            """
            SELECT pr.name, sum(tb.distance)
            FROM truck_booking AS tb
            INNER JOIN res_partner AS pr ON pr.id = tb.partner_id
            GROUP BY pr.id, pr.name
            """
        )
        customer = cr.dictfetchall()
        cust = [rec.get('name') for rec in customer]
        cust_sum = [rec.get('sum') for rec in customer]
        cr.execute(
            """
            SELECT fv.name, sum(tb.distance)
            FROM truck_booking AS tb
            INNER JOIN fleet_vehicle_model AS fv ON fv.id = tb.truck_id
            GROUP BY name
            """
        )
        truck = cr.dictfetchall()
        truck_name = [rec.get('name') for rec in truck]
        truck_sum = [rec.get('sum') for rec in truck]
        return {
            'cust': cust,
            'cust_sum': cust_sum,
            'truck_name': truck_name,
            'truck_sum': truck_sum,
        }

    @api.model
    def get_weight(self):
        """Function to get total weight of the goods."""
        cr = self.env.cr
        cr.execute(
            """
            SELECT pr.name, SUM(tb.weight)
            FROM truck_booking AS tb
            INNER JOIN res_partner AS pr ON pr.id = tb.partner_id
            GROUP BY pr.id, pr.name
            """
        )
        customer = cr.dictfetchall()
        cr.execute(
            """
            SELECT fv.name, SUM(tb.weight)
            FROM truck_booking AS tb
            INNER JOIN fleet_vehicle_model AS fv ON fv.id = tb.truck_id
            GROUP BY name
            """
        )
        truck = cr.dictfetchall()
        cust_sum = [record.get('sum') for record in customer]
        cust = [record.get('name') for record in customer]
        truck_sum = [record.get('sum') for record in truck]
        truck_name = [record.get('name') for record in truck]
        return {
            'cust': cust,
            'cust_sum': cust_sum,
            'truck_name': truck_name,
            'truck_sum': truck_sum
        }

    @api.model
    def get_select_filter(self, option):
        """Function to filter data on the basis of the selected period."""
        if option == 'year':
            create_date = (
                "create_date BETWEEN (now() - interval '1 year') AND now()"
            )
        elif option == 'month':
            create_date = (
                "create_date BETWEEN (now() - interval '1 months') AND now()"
            )
        elif option == 'week':
            create_date = (
                "create_date BETWEEN (now() - interval '7 day') AND now()"
            )
        elif option == 'day':
            create_date = (
                "create_date BETWEEN (now() - interval '1 day') AND now()"
            )
        else:
            return {}
        cr = self.env.cr
        cr.execute(
            "SELECT count(*) FROM truck_booking WHERE %s" % create_date
        )
        booking = cr.dictfetchall()
        cr.execute(
            "SELECT sum(distance) FROM truck_booking WHERE %s" % create_date
        )
        distance = cr.dictfetchall()
        cr.execute(
            "SELECT sum(amount) FROM truck_booking WHERE %s" % create_date
        )
        amount = cr.dictfetchall()
        cr.execute(
            "SELECT sum(amount) FROM truck_booking "
            "WHERE state = 'invoice' AND %s" % create_date
        )
        invoice = cr.dictfetchall()
        cr.execute(
            "SELECT fv.name, count(name) "
            "FROM truck_booking AS tb "
            "INNER JOIN fleet_vehicle_model AS fv ON fv.id = tb.truck_id "
            "WHERE tb.%s "
            "GROUP BY name ORDER BY count DESC LIMIT 10" % create_date
        )
        truck = cr.dictfetchall()
        cr.execute(
            "SELECT pr.name, count(pr.id) AS count "
            "FROM truck_booking AS tb "
            "INNER JOIN res_partner AS pr ON pr.id = tb.partner_id "
            "WHERE tb.%s "
            "GROUP BY pr.id, pr.name ORDER BY count DESC LIMIT 10" % create_date
        )
        customer = cr.dictfetchall()

        def fetch_group_sum(query):
            cr.execute(query % create_date)
            result = cr.dictfetchall()
            return [r.get('name') for r in result], [r.get('sum') for r in
                                                     result]
        cust_invoice_name, cust_invoice_sum = fetch_group_sum(
            "SELECT pr.name, sum(tb.amount) "
            "FROM truck_booking AS tb "
            "INNER JOIN res_partner AS pr ON pr.id = tb.partner_id "
            "WHERE tb.%s GROUP BY pr.id, pr.name"
        )
        truck_invoice_name, truck_invoice_count = fetch_group_sum(
            "SELECT fv.name, sum(tb.amount) "
            "FROM truck_booking AS tb "
            "INNER JOIN fleet_vehicle_model AS fv ON fv.id = tb.truck_id "
            "WHERE tb.%s GROUP BY name"
        )
        cust_distance_name, cust_distance_count = fetch_group_sum(
            "SELECT pr.name, sum(tb.distance) "
            "FROM truck_booking AS tb "
            "INNER JOIN res_partner AS pr ON pr.id = tb.partner_id "
            "WHERE tb.%s GROUP BY pr.id, pr.name"
        )
        truck_distance_name, truck_distance_count = fetch_group_sum(
            "SELECT fv.name, sum(tb.distance) "
            "FROM truck_booking AS tb "
            "INNER JOIN fleet_vehicle_model AS fv ON fv.id = tb.truck_id "
            "WHERE tb.%s GROUP BY name"
        )
        cust_weight_name, cust_weight_count = fetch_group_sum(
            "SELECT pr.name, sum(tb.weight) "
            "FROM truck_booking AS tb "
            "INNER JOIN res_partner AS pr ON pr.id = tb.partner_id "
            "WHERE tb.%s GROUP BY pr.id, pr.name"
        )
        truck_weight_name, truck_weight_count = fetch_group_sum(
            "SELECT fv.name, sum(tb.weight) "
            "FROM truck_booking AS tb "
            "INNER JOIN fleet_vehicle_model AS fv ON fv.id = tb.truck_id "
            "WHERE tb.%s GROUP BY name"
        )
        return {
            'booking': booking,
            'distance': distance,
            'amount': amount,
            'invoice': invoice,
            'truck': truck,
            'customer': customer,
            'cust_invoice_name': cust_invoice_name,
            'cust_invoice_sum': cust_invoice_sum,
            'truck_invoice_name': truck_invoice_name,
            'truck_invoice_count': truck_invoice_count,
            'cust_distance_name': cust_distance_name,
            'cust_distance_count': cust_distance_count,
            'truck_distance_name': truck_distance_name,
            'truck_distance_count': truck_distance_count,
            'cust_weight_name': cust_weight_name,
            'cust_weight_count': cust_weight_count,
            'truck_weight_name': truck_weight_name,
            'truck_weight_count': truck_weight_count,
        }
