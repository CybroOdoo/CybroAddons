# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Dilshad Tk  (odoo@cybrosys.com)
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
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PropertyRental(models.Model):
    """A class for the model property rental to represent
    the rental order of a property"""
    _name = 'property.rental'
    _description = 'Property Rent'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', readonly=True,
                       required=True, copy=False, default='New',
                       help='The reference code/sequence of the property '
                            'rental')
    property_id = fields.Many2one(
        'property.property', string='Property',
        required=True, copy=False,
        help='The property to be rented',
        domain="[('state','=','available'),('sale_rent','=','for_tenancy')]")
    owner_id = fields.Many2one('res.partner', string='Land Lord',
                               related='property_id.landlord_id', store=True,
                               help='The owner / land lord of the property')
    rent_price = fields.Monetary(string='Rent Price',
                                 related='property_id.rent_month',
                                 help='The Rental price per month of the '
                                      'property')
    renter_id = fields.Many2one('res.partner', string='Renter', required=True,
                                help='The customer who is renting the property')
    state = fields.Selection(
        [('draft', 'Draft'), ('in_contract', 'In Contract'),
         ('expired', 'Expired'), ('cancel', 'Cancelled')],
        required=True, default='draft', string='Status', tracking=True,
        help="* The \'Draft\' status is used when the rental is in draft.\n"
             "* The \'In Contract\' status is used when the property is rented "
             "and is in contract\n"
             "* The \'Expired\' status is used when the property rented "
             "contract has expired.\n"
             "* The \'Cancelled\' status is used when the property rental "
             "is cancelled.\n")
    start_date = fields.Date(string='Start Date', required=True,
                             help='The starting date of the rent')
    end_date = fields.Date(string='End Date', required=True,
                           help='The Ending date of the rent')
    invoice_count = fields.Integer(strinf='Invoice Count',
                                   compute='_compute_invoice_count',
                                   help='The Invoices related to this rental')
    rental_bills_ids = fields.One2many('rental.bill', 'rental_id')
    invoice_date = fields.Date(string='Invoice Date',
                               help='The latest Invoiced Date')
    next_invoice = fields.Date(string='Next Invoice',
                               compute='_compute_next_invoice',
                               help='The next invoicing date')
    company_id = fields.Many2one('res.company',
                                 string="Property Management Company",
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  related='company_id.currency_id')

    @api.model
    def create(self, vals):
        """Setting the sequence when record is created"""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'property.rent') or 'New'
        return super(PropertyRental, self).create(vals)

    def unlink(self):
        """Restricts deleting record"""
        for rec in self:
            if rec.state == 'in_contract':
                raise ValidationError(_("You can't delete property rental in In Contract state."))
            return super().unlink()

    def _compute_invoice_count(self):
        """Calculates the Invoice count for the property"""
        for rec in self:
            rec.invoice_count = self.env['account.move'].search_count(
                [('property_rental_id', '=', rec.id)])

    def _compute_next_invoice(self):
        """Computes the next_invoice date"""
        for rec in self:
            if rec.invoice_date and fields.Date.today() < rec.end_date:
                rec.next_invoice = fields.Date.add(rec.invoice_date, months=1)
            else:
                rec.next_invoice = False

    def action_cancel(self):
        """ Changes the record stage to cancel """
        self.property_id.state = 'available'
        self.state = 'cancel'

    def action_create_contract(self):
        """Creates an invoice for contract. Checks if the customer
        is blacklisted."""
        if self.renter_id.blacklisted:
            raise ValidationError(
                _('The Customer %r is Blacklisted.', self.renter_id.name))
        if self.property_id.state == 'rented':
            raise ValidationError(
                _('%r is already rented.', self.property_id.name))
        self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.renter_id.id,
            'property_rental_id': self.id,
            'invoice_line_ids': [fields.Command.create({
                'name': self.property_id.name,
                'price_unit': self.rent_price,
                'currency_id': self.env.user.company_id.currency_id.id,
            })]
        })
        self.invoice_date = fields.Date.today()
        self.property_id.state = 'rented'
        self.state = 'in_contract'

    def action_view_invoice(self):
        """Views all the related invoice in tree view related to the records"""
        return {
            'name': _('Invoices'),
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'target': 'current',
            'type': 'ir.actions.act_window',
            'domain': [('property_rental_id', '=', self.id),
                       ('move_type', '=', 'out_invoice')]
        }

    @api.model
    def action_check_rental(self):
        """Scheduled action to create the next invoice for rent
        else set it as expired."""
        records = self.env['property.rental'].search(
            [('state', '=', 'in_contract')])
        for rec in records:
            if not rec.next_invoice:
                rec.state = 'expired'
            if fields.Date.today() == rec.next_invoice:
                self.env['account.move'].create({
                    'move_type': 'out_invoice',
                    'property_rental_id': rec.id,
                    'invoice_line_ids': [fields.Command.create({
                        'name': rec.property_id.name,
                        'price_unit': rec.rent_price,
                        'currency_id': rec.env.user.company_id.currency_id.id,
                    })]
                })
                rec.invoice_date = fields.Date.today()
