# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Vishnu KP @ Cybrosys, (odoo@cybrosys.com)
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

################################################################################
from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError
from datetime import date


class SaleConsignment(models.Model):
    _name = "sale.consignment"
    _description = "Sale Consignment"
    _inherit = ['mail.activity.mixin', 'mail.thread']

    @api.model
    def _settings_domain(self):
        customer_domain = self.env['ir.config_parameter'].get_param(
            'sale_consignment.consignment_product_only')
        return customer_domain

    @api.model
    def _default_destination(self):
        location_dest_id = self.env['ir.config_parameter'].get_param(
            'sale_consignment.location_dest_id')
        return int(location_dest_id)

    @api.depends('customer_domain')
    def _partner_domain(self):
        if self.env['ir.config_parameter'].get_param(
                'sale_consignment.consignment_customer_only'):
            return [('is_consignment', '=', True)]
        else:
            return []

    name = fields.Char(string='Name', help="Sequence of the consignment Sale",
                       default='New')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)
    partner_id = fields.Many2one('res.partner', string='Customer',
                                 domain=lambda self: self._partner_domain(),
                                 help="Partner Name", required=True)

    end_date = fields.Date(string='Expiry Date',
                           help="Expiry date of the sale consignment",
                           required=True)
    date = fields.Date(string='Date', default=date.today(),
                       help="Date of the sale consignment", required=True)
    price_list_id = fields.Many2one('product.pricelist', string='Price List',
                                    compute='_compute_partner_id')
    state = fields.Selection(
        selection=[('draft', 'Draft'), ('confirm', 'Confirm')],
        default="draft")
    user_id = fields.Many2one("res.users", string='Sales Person',
                              default=lambda self: self.env.user,
                              required=True)
    consignment_line_ids = fields.One2many('sale.consignment.line',
                                           'consignment_id',
                                           string='Order Line')
    location_id = fields.Many2one(
        'stock.location', 'Source Location',
        help="Location where the product you want to pickup from.",
        domain="[('usage','=','internal')]",
        required=True)
    sale_count = fields.Integer(string='Sale Order',
                                compute='_compute_sale_count')
    picking_count = fields.Integer(string='Picking Order',
                                   compute='_compute_picking_count')
    sale_order_id = fields.Many2one('sale.order')
    ware_house_id = fields.Many2one('stock.warehouse',
                                    string='Warehouse',
                                    related='location_id.warehouse_id',
                                    help='Choose the Warehouse')
    condition_check = fields.Char(string='')
    customer_domain = fields.Boolean(
        default=lambda self: self._settings_domain())
    location_dest_id = fields.Many2one(
        'stock.location', 'Destination Location',
        required=True,
        default=lambda self: self._default_destination(),
        help="Location where you want to send the product.")

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'sale.consignment') or _('New')
        res = super(SaleConsignment, self).create(vals)
        return res

    @api.depends('consignment_line_ids')
    def _compute_sale_count(self):
        for rec in self:
            rec.sale_count = self.env['sale.order'].search_count([
                ('consignment_id', '=', rec.id)])

    @api.depends('consignment_line_ids')
    def _compute_picking_count(self):
        for rec in self:
            rec.picking_count = self.env['stock.picking'].search_count([
                ('consignment_id', '=', rec.id)])

    @api.depends('partner_id')
    def _compute_partner_id(self):
        self.price_list_id = self.partner_id.property_product_pricelist.id

    def action_order_confirm(self):
        picking_type = self.env['stock.picking.type'].search(
            [('code', '=', 'internal'),
             ('warehouse_id', '=', self.ware_house_id.id),
             ('company_id', '=', self.env.company.id),
             ('default_location_src_id.usage', '=', 'internal'),
             ('default_location_dest_id.usage', '=', 'transit'),
             ], limit=1)
        if not picking_type:
            raise UserError(_(
                "There is no available Operation type like destination "
                "to transit location Please create and try again"))
        else:
            self.env['stock.picking'].create({
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
                'partner_id': self.partner_id.id,
                'picking_type_id': picking_type.id,
                'consignment_id': self.id,
                'move_ids': [
                    Command.create({
                        'name': self.name,
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.demand_quantity,
                        'location_id': self.location_id.id,
                        'location_dest_id': self.location_dest_id.id,
                    }) for line in self.consignment_line_ids]
            }).action_confirm()

            self.write({'state': 'confirm'})

    def create_sale_order(self):
        self.sale_order_id = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'consignment_id': self.id,
            'user_id': self.user_id.id,
            'order_line': [
                Command.create({
                    'product_id': line.product_id.id,
                    'product_uom': line.product_id.uom_id.id,
                    'product_uom_qty': 1.0,
                }) for line in self.consignment_line_ids]
        }).id
        return {
            'name': 'Sale Order',
            'view_mode': 'form',
            'res_id': self.sale_order_id.id,
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'target': 'current'
        }

    def action_view_order(self):
        return {
            'name': 'Sale Order',
            'view_mode': 'tree,form',
            'domain': [('consignment_id', 'in', [rec.id for rec in self])],
            'context': {'create': False},
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'target': 'current'
        }

    def action_view_pickings(self):
        return {
            'name': 'Picking Order',
            'view_mode': 'tree,form',
            'domain': [('consignment_id', 'in', [rec.id for rec in self])],
            'context': {'create': False},
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'target': 'current'
        }

    def mail_update_to_salesman(self):
        orders = self.env['sale.consignment'].search(
            [('end_date', '=', date.today())])
        for rec in orders:
            mail_template_id = 'sale_consignment.sale_consignment_expiry'
            rendered_body = self.env['ir.qweb']._render(mail_template_id,
                                                        {'expiry': rec})
            body = self.env['mail.render.mixin']._replace_local_links(
                rendered_body)
            self.env['mail.mail'].sudo().create({
                'author_id': self.env.user.partner_id.id,
                'auto_delete': True,
                'body_html': body,
                'email_from': self.env.user.partner_id.email,
                'email_to': rec.user_id.partner_id.email,
                'subject': 'Reminder: Sale Consignment Date Expired',
            }).send()
