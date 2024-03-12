# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
################################################################################
import itertools
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    """Inherits Sales"""
    _inherit = "sale.order"

    is_version = fields.Boolean(string="Is Version",
                                help="For checking version or not")
    version_count = fields.Integer(string="Sale Version Count",
                                   compute='_compute_version_count',
                                   help="Count of version created")
    current_version_id = fields.Many2one("sale.order",
                                         string="Current Version",
                                         help="For creating versions")
    version_ids = fields.One2many("sale.order",
                                  string="Version",
                                  inverse_name="current_version_id",
                                  help="Versions created")
    quotation_ref = fields.Char(string='Quotation Reference',
                                copy=False, readonly=True, tracking=True,
                                help="Quotation Reference")
    state = fields.Selection(
        selection_add=[('waiting_for_approval', 'Waiting For Approval'),
                       ('sale',)])
    approval_user_id = fields.Many2one('res.users',
                                       string='Discount Approved By',
                                       help="Discount approving person.")
    onhand_check = fields.Boolean(string='Enable OnHand',
                                  help='To check whether it is based on'
                                       ' on hand quantity')
    forecast_check = fields.Boolean(string='Enable Forecast',
                                    help='To check whether it is based on'
                                         ' Forecast quantity')
    automate_print_invoices = fields.Boolean(
        string='Print Invoices',
        help="Print invoices for corresponding sale orders")
    signature = fields.Binary(string='Signature',
                              help="Field for adding "
                                   "the signature of the "
                                   "sales person")
    check_signature = fields.Boolean(compute='_compute_check_signature',
                                     help="To check signature approval is "
                                          "needed")
    settings_approval = fields.Boolean(compute='_compute_settings_approval',
                                     help="To check signature approval is "
                                       "enabled in settings")
    active = fields.Boolean(string='Active', help='Active', default=True)
    user_salesperson = fields.Boolean(string="User Salesperson",
                                      compute="_compute_user_salesperson",
                                      help="Check if user is salesperson")

    @api.depends('user_salesperson')
    def _compute_user_salesperson(self):
        """Computes the user_salesperson field based on login user"""
        for rec in self:
            if rec.user_id == rec.env.user:
                rec.user_salesperson = True
            else:
                rec.user_salesperson = False

    @api.depends('signature')
    def _compute_check_signature(self):
        """In this function computes the value of
        the boolean field check signature
        which is used to hide/unhide the validate
         button in the current document"""
        if self.env['ir.config_parameter'].sudo().get_param(
                'all_in_one_sales_kit.sale_document_approve'):
            if self.signature:
                self.check_signature = True
            else:
                self.check_signature = False
        else:
            self.check_signature = True

    def action_create_versions(self):
        """For creating the versions of the sale order"""
        sale_order_copy_id = self.copy()
        sale_order_copy_id.is_version = True
        length = len(self.version_ids)
        sale_order_copy_id.name = "%s-%s" % (self.name, str(length + 1))

        self.write({'version_ids': [(4, sale_order_copy_id.id)]})

    @api.depends('version_ids')
    def _compute_version_count(self):
        """For calculating the number of versions created"""
        for sale in self:
            sale.version_count = len(sale.version_ids)

    @api.depends('partner_id')
    def _compute_settings_approval(self):
        """Computes the settings_approval field based on settings field."""
        for rec in self:
            if rec.env['ir.config_parameter'].sudo().get_param(
                    'all_in_one_sales_kit.sale_document_approve'):
                rec.settings_approval = True
            else:
                rec.settings_approval = False

    def action_view_versions(self):
        """Action for viewing versions"""
        action = {
            "type": "ir.actions.act_window",
            "view_mode": "kanban,tree,form",
            "name": _("Sale Order Versions"),
            "res_model": self._name,
            "domain": [('id', 'in', self.version_ids.ids)],
            "target": "current",
        }
        return action

    def action_confirm(self):
        """Override the confirm button of the sale order for cancelling the
        other versions and making the current version main,also method for
         confirming the sale order discount and sending mail for the approving
         person if approval limit crossed.Super the method create to confirm
          quotation, create and validate invoice"""
        res = super().action_confirm()
        automate_invoice = self.env[
            'ir.config_parameter'].sudo().get_param(
            'automate_invoice')
        automate_print_invoices = self.env[
            'ir.config_parameter'].sudo().get_param(
            'automate_print_invoices')
        automate_validate_invoice = self.env[
            'ir.config_parameter'].sudo().get_param(
            'automate_validate_invoice')
        if automate_print_invoices:
            self.automate_print_invoices = True
        if automate_invoice:
            self._create_invoices()
            if automate_validate_invoice:
                self.invoice_ids.action_post()
        if not self.version_ids:
            parent_sale = self.current_version_id
            versions = parent_sale.mapped('version_ids').ids
            if versions:
                versions.append(parent_sale.id)
            for version in parent_sale.version_ids:
                if version.state == 'sale':
                    # Updating the version name into main version name and
                    # other versions state into cancel
                    version.current_version_id.update({'is_version': True,
                                                       'state': 'cancel'})
                    version.update({'version_ids': versions,
                                    "name": version.current_version_id.name,
                                    'is_version': False})
                if version.state == 'draft':
                    version.update({'state': 'cancel'})
        else:
            if self.state == 'sale':
                for sale in self.version_ids:
                    sale.update({'state': 'cancel'})
        low_qty = ["Can't confirm the sale order due to: \n"]
        for rec in self.order_line:
            product_restriction = self.env[
                'ir.config_parameter'].sudo().get_param(
                'sale_stock_restrict.product_restriction')
            check_stock = self.env[
                'ir.config_parameter'].sudo().get_param(
                'sale_stock_restrict.check_stock')
            if product_restriction:
                if rec.product_id.detailed_type == 'product':
                    if check_stock == 'on_hand_quantity':
                        if rec.product_uom_qty > rec.qty_available:
                            self.onhand_check = True
                            onhand_qty_list = "You have added %s units of %s" \
                                              " but you only have %s units" \
                                              " available.\n" % (
                                                  rec.product_uom_qty,
                                                  rec.product_id.name,
                                                  rec.qty_available)
                            low_qty.append(onhand_qty_list)

                    if check_stock == 'forecast_quantity':
                        if rec.product_uom_qty > rec.forecast_quantity:
                            self.forecast_check = True
                            forecast_qty_list = "You have added %s" \
                                                " units of %s but " \
                                                "you only have" \
                                                " %s units available.\n" % (
                                                    rec.product_uom_qty,
                                                    rec.product_id.name,
                                                    rec.forecast_quantity)
                            low_qty.append(forecast_qty_list)
        listToStr = ' '.join(map(str, low_qty))
        if self.onhand_check:
            raise UserError(listToStr)
        if self.forecast_check:
            raise UserError(listToStr)
        to_approve = False
        discount_vals = self.order_line.mapped('discount')
        approval_users = self.env.ref(
            'all_in_one_sales_kit.group_approval_manager').users
        user_discount = self.env.user.allow_discount
        if self.env.user.discount_control == True:
            for rec in discount_vals:
                if rec > user_discount:
                    to_approve = True
                    break
        if to_approve:
            display_id = self.id
            action_id = self.env.ref(
                'sale.action_quotations_with_onboarding').id
            base_url = self.env['ir.config_parameter'].sudo().get_param(
                'web.base.url')
            redirect_link = "/web#id=%s&cids=1&menu_id=178&action=%s" \
                            "&model" \
                            "=sale.order&view_type=form" % (
                                display_id, action_id)
            url = base_url + redirect_link
            for user in approval_users:
                mail_body = """
                        <p>Hello,</p>
                               <p>New sale order '%s' 
                               Created with Discount by '%s' 
                               need your approval on it.</p>
                               <p>To Approve, Cancel Order,
                                Click on the Following 
                               Link:
                               <a href='%s' style="display: inline-block; 
                               padding: 10px; text-decoration: none; 
                               font-size: 12px;
                               background-color: #875A7B; color: #fff; 
                               border-radius: 5px;">
                               <strong>Click Me</strong></a>
                               </p>
                               <p>Thank You.</p>""" % (self.name,
                                                       self.env.user.name,
                                                       url)
                mail_values = {
                    'subject': "'%s' Discount Approval Request" % (self.name),
                    'body_html': mail_body,
                    'email_to': user.partner_id.email,
                    'model': 'sale.order',
                }
                mail_id = self.env['mail.mail'].sudo().create(mail_values)
                mail_id.sudo().send()
            self.state = 'waiting_for_approval'
        for line in self.order_line:
            if line.product_id.is_pack:
                for record in line.product_id.pack_products_ids:
                    dest_loc = self.env.ref(
                        'stock.stock_location_customers').id
                    self.env['stock.move'].create({
                        'name': record.product_id.name,
                        'product_id': record.product_id.id,
                        'product_uom_qty':
                            record.quantity * line.product_uom_qty,
                        'product_uom': record.product_id.uom_id.id,
                        'picking_id': self.picking_ids[0].id,
                        'location_id':
                            self.picking_ids.picking_type_id.default_location_src_id.id,
                        'location_dest_id': dest_loc,
                    })
            return res

    @api.model
    def create(self, vals):
        """Method for generating sequence for quotation """
        res = super(SaleOrder, self).create(vals)
        seq_val = self.env.ref(
            'all_in_one_sales_kit.seq_quotation').id
        res.quotation_ref = self.env['ir.sequence'].browse(
            seq_val).next_by_id()
        return res

    def action_waiting_approval(self):
        """Method for approving the sale order discount"""
        self.approval_user_id = self.env.user.id
        self.state = 'sale'

    def action_print_invoice(self):
        """Method to print invoice"""
        data = self.invoice_ids
        return self.env.ref('account.account_invoices').report_action(data)

    @api.model
    def get_data(self):
        """To get data to the sales dashboard."""
        domain = [('user_id', '=', self.env.user.id)]
        quotation = self.env['sale.order'].search(
            domain + [('state', '=', 'draft')])
        my_sale_order_templates = self.env['sale.order'].search(
            domain + [('state', '=', 'sale')])
        quotation_sent = self.env['sale.order'].search(
            domain + [('state', '=', 'sent')])
        quotation_cancel = self.env['sale.order'].search(
            domain + [('state', '=', 'cancel')])
        customers = self.env['res.partner'].search([])
        to_invoice = self.env['sale.order'].search(
            domain + [('invoice_status', '=', 'to invoice')])
        products = self.env['product.template'].search([])
        return {
            'quotation': len(quotation),
            'my_sale_order_templates': len(my_sale_order_templates),
            'quotation_sent': len(quotation_sent),
            'quotation_cancel': len(quotation_cancel),
            'customers': len(customers),
            'products': len(products),
            'to_invoice': len(to_invoice),
        }

    @api.model
    def get_value(self, start_date, end_date):
        """It is to pass values according to start and end date to the
        dashboard."""
        if start_date and end_date:
            domain = [('user_id', '=', self.env.user.id),
                      ('date_order', '>=', start_date),
                      ('date_order', '<=', end_date)]
        elif start_date:
            domain = [('user_id', '=', self.env.user.id),
                      ('date_order', '>=', start_date)]
        elif end_date:
            domain = [('user_id', '=', self.env.user.id),
                      ('date_order', '<=', end_date)]

        quotation = self.env['sale.order'].search(
            domain + [('state', '=', 'draft')])
        my_sale_order_templates = self.env['sale.order'].search(
            domain + [('state', '=', 'sale')])
        quotation_sent = self.env['sale.order'].search(
            domain + [('state', '=', 'sent')])
        quotation_cancel = self.env['sale.order'].search(
            domain + [('state', '=', 'cancel')])
        customers = self.env['res.partner'].search([])
        products = self.env['product.template'].search([])
        to_invoice = self.env['sale.order'].search(
            domain + [('invoice_status', '=', 'to invoice')])
        return {
            'quotation': len(quotation),
            'my_sale_order_templates': len(my_sale_order_templates),
            'quotation_sent': len(quotation_sent),
            'quotation_cancel': len(quotation_cancel),
            'customers': len(customers),
            'products': len(products),
            'to_invoice': len(to_invoice),
        }

    @api.model
    def get_lead_customer(self):
        """Returns customer data to the graph of dashboard"""
        lead_template = {}
        sale = {}
        partner_id = self.env['res.partner'].sudo().search([])
        vals = self.env['sale.order'].sudo().search([
        ]).mapped('partner_id').ids
        for record in partner_id:
            if record.id in vals:
                record.ref = vals.count(record.id)
                sale.update({record: vals.count(record.id)})
        sort = dict(
            sorted(sale.items(), key=lambda item: item[1], reverse=True))
        out = dict(itertools.islice(sort.items(), 10))
        for count in out:
            lead_template[count.name] = out[count]
        return {
            'lead_templates': lead_template,
        }

    @api.model
    def get_lead_product(self):
        """Returns product data to the graph of dashboard"""
        lead_template = {}
        sale = {}
        product_id = self.env['product.template'].search([])
        for record in product_id:
            sale.update({record: record.sales_count})
        sort = dict(
            sorted(sale.items(), key=lambda item: item[1], reverse=True))
        out = dict(itertools.islice(sort.items(), 10))
        for product in out:
            lead_template[product.name] = out[product]
        return {
            'lead_templates': lead_template,
        }

    @api.model
    def get_lead_order(self):
        """Returns lead sale order data to the graph of dashboard"""
        lead_template = {}
        sale = {}
        order_id = self.env['sale.order'].search([('state', '=', 'sale')])
        for record in order_id:
            sale.update({record: record.amount_total})
        sort = dict(
            sorted(sale.items(), key=lambda item: item[1], reverse=True))
        out = dict(itertools.islice(sort.items(), 10))
        for order in out:
            lead_template[order.name] = out[order]
        return {
            'lead_templates': lead_template,
        }

    @api.model
    def get_my_monthly_comparison(self):
        """Returns my monthly sale count data to the graph of dashboard"""
        lead_template = {}
        sales_order = self.env['sale.order'].search(
            [('user_id', '=', self.env.user.id)])
        list = [rec.date_order.month for rec in sales_order]
        for i in range(1, 13):
            count = list.count(i)
            lead_template.update({
                i: count
            })
        return {
            'lead_templates': lead_template,
        }

    @api.model
    def get_sales_team(self):
        """Returns sales team data to the graph of dashboard"""
        lead_template = {}
        sale = {}
        sales_team = self.env['crm.team'].search([])
        for record in sales_team:
            total = sum(self.env['sale.order'].search(
                [('state', '=', 'sale'),
                 ('team_id', '=', record.id)]).mapped('amount_total'))
            sale.update({record: total})
        sort = dict(
            sorted(sale.items(), key=lambda item: item[1], reverse=True))
        out = dict(itertools.islice(sort.items(), 10))
        for team in out:
            lead_template[team.name] = out[team]
        return {
            'lead_templates': lead_template,
        }

    @api.model
    def get_least_sold(self):
        """Returns least sold product data to the graph of dashboard"""
        lead_template = {}
        sale = {}
        product_id = self.env['product.template'].search([])
        for record in product_id:
            if record.sales_count != 0:
                sale.update({record: record.sales_count})
        sort = dict(
            sorted(sale.items(), key=lambda item: item[1], reverse=False))
        out = dict(itertools.islice(sort.items(), 10))
        for product in out:
            lead_template[product.name] = out[product]
        return {
            'lead_templates': lead_template,
        }
