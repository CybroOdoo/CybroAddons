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
from datetime import timedelta
from odoo import api, fields, models


class HospitalVaccination(models.Model):
    """Class holding Vaccination details"""
    _name = 'hospital.vaccination'
    _description = "Vaccination Details"
    _order = 'name desc'

    name = fields.Char(string='Vaccination Reference', copy=False,
                       readonly=True, index=True, help='Name of vaccination',
                       default=lambda self: 'New')
    patient_id = fields.Many2one('res.partner',
                                 domain=[('patient_seq', 'not in',
                                          ['New', 'Employee', 'User'])],
                                 required=True,
                                 help='Choose the patient')
    vaccine_date = fields.Date(string='Vaccination Date', help='Date of '
                                                               'vaccination',
                               default=fields.Date.context_today)
    dose = fields.Float(help='Dose of the vaccine')
    vaccine_product_id = fields.Many2one('product.template',
                                         domain="[('vaccine_ok', '=', True)]",
                                         string="Vaccine", help='Choose the '
                                                                'vaccine',
                                         required=True)
    vaccine_price = fields.Float(related='vaccine_product_id.list_price',
                                 string="Price", help='Price of vaccine')
    sale_order_id = fields.Many2one('sale.order',
                                    help='Sale order for the vaccine')
    sold = fields.Boolean(help='True if sale order created')
    certificate = fields.Binary(help='Vaccination '
                                                           'certificate')
    attachment_id = fields.Many2one('ir.attachment',
                                    help='Attachments added to the vaccination')
    recurring_vaccine = fields.Boolean(help='True for recurring vaccinations')
    total_vaccine = fields.Integer(string="Total Dose",
                                   help='Total number of vaccines')
    next_vaccine_days = fields.Integer(string="Next Vaccine (In Days)",
                                       help='The number of days to next '
                                            'vaccine')
    next_vaccine = fields.Date(string="Next Vaccination Date",
                               help='Date of next '
                                    'vaccine',
                               readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        """Create sequence in hospital vaccination"""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('vaccination.sequence') or 'New'
        return super().create(vals_list)

    @api.onchange('next_vaccine_days')
    def _onchange_next_vaccine_days(self):
        """Method for updating the field next_vaccine according to the value
        of next_vaccine_days"""
        if self.next_vaccine_days:
            self.sudo().write({'next_vaccine': fields.Date.today() + timedelta(
                self.next_vaccine_days)})

    def action_create_so(self):
        """Method for creating the sale order for vaccines"""
        product_id = self.env['product.product'].sudo().search([
            ('product_tmpl_id', '=', self.vaccine_product_id.id)
        ])
        sale = self.env['sale.order'].search([
            ('partner_id', '=', self.patient_id.id),
            ('state', '=', 'draft')], limit=1)
        if sale:
            sale.sudo().write({
                'order_line': [(
                    0, 0, {
                    'product_id': product_id[0].id,
                    'name': self.vaccine_product_id.name,
                    'price_unit': self.vaccine_price,
                    'product_uom_qty': self.dose
                }
                )]
            })
        else:
            sale = self.env['sale.order'].sudo().create({
                'partner_id': self.patient_id.id,
                'date_order': fields.Date.today(),
                'order_line': [(0, 0, {
                    'product_id': product_id[0].id,
                    'name': self.vaccine_product_id.name,
                    'price_unit': self.vaccine_price,
                    'product_uom_qty': self.dose
                })]
            })
        self.sold = True
        self.sale_order_id = sale.id

    def action_get_sale_order(self):
        """Smart button action for viewing corresponding sale orders"""
        return {
            'name': 'Sale order',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
            'res_id': self.sale_order_id.id
        }

    @api.model
    def fetch_vaccination_data(self, **kwargs):
        """Method for fetching vaccine data"""
        data = self.sudo().search(kwargs['domain'])
        context = []
        for rec in data:
            attachment = self.env['ir.attachment'].sudo().search([
                ('res_id', '=', rec.id),
                ('res_model', '=', 'hospital.vaccination'),
            ], limit=1)
            attachment_id = attachment.id if attachment else False
            context.append({
                'id': rec.id,
                'name': rec.name,
                'patient_id': [rec.patient_id.id,
                               rec.patient_id.name],
                'vaccine_product_id': rec.vaccine_product_id.name,
                'vaccine_price': rec.vaccine_price,
                'attachment_id': attachment_id,
                'view_id': self.env['ir.ui.view'].sudo().search([
                    ('name', '=', 'hospital.vaccination.view.form')]).id
            })
        return context
