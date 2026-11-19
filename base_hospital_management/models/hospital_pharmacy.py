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
from odoo import api, fields, models


class HospitalPharmacy(models.Model):
    """Class holding Pharmacy details."""
    _name = 'hospital.pharmacy'
    _description = 'Pharmacy'

    name = fields.Char(help='Name of the pharmacy',
                       required=True)
    pharmacist_id = fields.Many2one('hr.employee',
                                    help='Name of the pharmacist',
                                    domain=[
                                        ('job_id.name', '=', 'Pharmacist')])
    phone = fields.Char(help='Phone number of the pharmacy')
    mobile = fields.Char(help='Mobile number of the pharmacy')
    email = fields.Char(help='Email of the pharmacy')
    street = fields.Char(help='Street of pharmacy')
    street2 = fields.Char(help='Street2 of pharmacy')
    zip = fields.Char(help='Zip code of pharmacy')
    city = fields.Char(help='City of pharmacy')
    state_id = fields.Many2one("res.country.state",
                               help='State of pharmacy')
    country_id = fields.Many2one('res.country',
                                 help='Country of pharmacy')
    notes = fields.Text(help='Notes regarding pharmacy')
    image_129 = fields.Image(string='Image', help='Image of pharmacy',
                             max_width=128, max_height=128)
    active = fields.Boolean(help='True for active pharmacy',
                            default=True)
    medicine_ids = fields.One2many('pharmacy.medicine',
                                   'pharmacy_id',
                                   string='Pharmacy',
                                   help='Indicates the medicines in the '
                                        'pharmacy')
    sales_team_id = fields.Many2one('crm.team',
                                    help='Choose the sales-team for the'
                                         ' pharmacy')

    @api.model_create_multi
    def create(self, vals_list):
        """Method for creating CRM team"""
        for vals in vals_list:
            team_id = self.env['crm.team'].sudo().create({
                'name': vals['name'] + ' Pharmacy Team',
                'company_id': False,
                'user_id': self.env.uid
            })
            vals['sales_team_id'] = team_id.id
        return super().create(vals_list)

    @api.model
    def create_sale_order(self, kwargs):
        """Creating sale order from pharmacy dashboard"""
        partner_obj = self.env['res.partner'].sudo()
        patient_id = False

        # 1. If explicit patient_id passed from frontend search
        if kwargs.get('patient_id'):
            patient = partner_obj.browse(int(kwargs['patient_id']))
            if patient.exists():
                patient_id = patient

        # 2. If patient_code / sequence passed
        if not patient_id and kwargs.get('patient_code'):
            patient_id = partner_obj.search([
                ('patient_seq', '=ilike', str(kwargs['patient_code']).strip()),
                ('patient_seq', 'not in', ['New', 'Employee', 'User'])
            ], limit=1)

        # 3. If OP reference passed
        if not patient_id and kwargs.get('op'):
            op_rec = self.env['hospital.outpatient'].sudo().search(
                [('op_reference', '=', kwargs['op'])], limit=1)
            if op_rec and op_rec.patient_id:
                patient_id = op_rec.patient_id

        # 4. Search existing patient by name / email / phone
        if not patient_id:
            name = (kwargs.get('name') or '').strip()
            email = (kwargs.get('email') or '').strip()
            phone = (kwargs.get('phone') or '').strip()
            patient_domain = [('patient_seq', 'not in', ['New', 'Employee', 'User'])]

            if name and email:
                patient_id = partner_obj.search(
                    [('name', '=ilike', name), ('email', '=ilike', email)] + patient_domain, limit=1)
            if not patient_id and name and phone:
                patient_id = partner_obj.search(
                    [('name', '=ilike', name), ('phone', '=ilike', phone)] + patient_domain, limit=1)
            if not patient_id and email:
                patient_id = partner_obj.search(
                    [('email', '=ilike', email)] + patient_domain, limit=1)
            if not patient_id and phone:
                patient_id = partner_obj.search(
                    [('phone', '=ilike', phone)] + patient_domain, limit=1)
            if not patient_id and name:
                patient_id = partner_obj.search(
                    [('name', '=ilike', name)] + patient_domain, limit=1)

        # 5. Only create if patient does not exist anywhere
        if not patient_id:
            patient_id = partner_obj.create({
                'name': kwargs.get('name'),
                'email': kwargs.get('email') or False,
                'phone': kwargs.get('phone') or False,
                'date_of_birth': kwargs.get('dob') or False,
                'gender': kwargs.get('gender') or 'male',
            })
        else:
            # Update missing details on the existing patient if provided
            update_vals = {}
            if kwargs.get('email') and not patient_id.email:
                update_vals['email'] = kwargs['email']
            if kwargs.get('phone') and not patient_id.phone:
                update_vals['phone'] = kwargs['phone']
            if kwargs.get('dob') and not patient_id.date_of_birth:
                update_vals['date_of_birth'] = kwargs['dob']
            if kwargs.get('gender') and not patient_id.gender:
                update_vals['gender'] = kwargs['gender']
            if update_vals:
                patient_id.write(update_vals)

        pharmacy_sale_order = self.env['sale.order'].sudo().create({
            'partner_id': patient_id.id,
        })
        for rec in kwargs.get('products', []):
            product = self.env['product.product'].sudo().search([
                ('product_tmpl_id', '=', int(rec['product']))
            ], limit=1)
            if not product:
                continue
            price_unit = float(rec['price']) if 'price' in rec and rec['price'] else product.list_price
            pharmacy_sale_order.sudo().write({
                'order_line': [(0, 0, {
                    'product_id': product.id,
                    'product_uom_qty': float(rec.get('qty', 1)),
                    'price_unit': price_unit,
                })]
            })
        pharmacy_sale_order.action_confirm()
        if 'op' in kwargs.keys():
            self.env['hospital.outpatient'].sudo().search(
                [('op_reference', '=', kwargs['op'])]).write(
                {
                    'is_sale_created': True
                })
        return {'invoice_id': pharmacy_sale_order.id, 'invoice': pharmacy_sale_order.name}

    @api.model
    def company_currency(self):
        """Currency symbol of current company"""
        return self.env.company.currency_id.symbol

    @api.model
    def tax_amount(self, kw):
        """Amount in tax of selected product in pharmacy"""
        return {
            'amount': self.env['account.tax'].sudo().browse(kw).amount
        }

    def action_get_inventory(self):
        """Inventory adjustment for medicine"""
        products = self.env['product.product'].sudo().search([
            ('product_tmpl_id', 'in', self.medicine_ids.product_id.ids)
        ])
        med_list = products.ids
        return {
            'name': 'medicine',
            'domain': ['&', ('product_id', 'in', med_list),
                       ('location_id.usage', '=', 'internal')],
            'type': 'ir.actions.act_window',
            'res_model': 'stock.quant',
            'view_id': self.env.ref(
                'stock.view_stock_quant_tree_inventory_editable').id,
            'view_mode': 'list',
        }

    def action_get_sale_order(self):
        """Sale order view of medicine"""
        return {
            'name': 'Sales',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('team_id', '=', self.sales_team_id.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_team_id': self.sales_team_id.id}
        }

    def fetch_sale_orders(self):
        """Method to fetch all sale orders for displaying on pharmacy
        dashboard"""
        return self.env['sale.order'].search_read(
            [('partner_id.patient_seq', 'not in', ['New', 'Employee',
                                                   'User'])],
            fields=['name', 'create_date', 'partner_id', 'amount_total',
                    'state'])
