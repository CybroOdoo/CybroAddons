# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class PosKeyboardShortcut(models.Model):
    """Store POS keyboard shortcut settings used by the Point of Sale UI."""
    _name = 'pos.keyboard.shortcut'
    _description = 'Pos Keyboard Shortcut'
    _inherit = ['pos.load.mixin']

    name = fields.Char(string='Reference Number',
                       default=lambda self: _('New'),
                       readonly=True, copy=False, help='Name')
    customer_screen = fields.Char(string='Customer Screen', default='C',
                                  help='Customer Screen')
    next_screen = fields.Char(string='Next Screen', default='Z', help='Next '
                                                                      'screen')
    select_qty = fields.Char(string='Select Quantity', default='Q',
                             help='To select quantity')
    select_discount = fields.Char(string='Select Discount', default='D',
                                  help='To select discount')
    select_price = fields.Char(string='Select Price', default='P',
                               help='To select the price')
    delete_orderlines = fields.Char(string='Delete Orderlines',
                                    default='Backspace', readonly=True,
                                    help='To delete orderlines')
    print_receipt = fields.Char(string='Print Receipt', default='R',
                                help='To print receipt')
    next_screen_show = fields.Char(string="Show Next Screen", default='Enter',
                                   readonly=True, help='To show the next '
                                                       'screen')
    back_screen = fields.Char(string='Back Screen', default="B", help='Back '
                                                                      'screen')
    click_ok = fields.Char(string='Ok Button of Popup', default='Enter',
                           readonly=True, help='Ok button of popup')
    select_user = fields.Char(string='Select POS user', default='U',
                              help='To select POS User')
    select_invoice = fields.Char(string='Order Invoice', default='I',
                                 help='To select invoice')
    close_pos = fields.Char(string='Close Pos Session', default='M',
                            help='To Close POS Session')
    click_cancel = fields.Char(string='Cancel Button in Popup', default='Esc',
                               readonly=True, help='To Cancel')
    payment_method_key_ids = fields.One2many(
        'pos.payment.method.key',
        inverse_name='keyboard_shortcut_id')
    validate_order = fields.Char(string='Validate Order', default='V',
                                 readonly=True, help='To validate order')
    new_order = fields.Char(string='New Order', default='X',
                            help='To new order')
    resume_order = fields.Char(string='Resume Order', default='S',
                               help='To Resume Order')
    sent_email = fields.Char(string='Sent Email', default='Y',
                             help='To Sent Email')


    @api.model
    def _load_pos_data_domain(self, data):
        """Return the record domain used when loading POS shortcut data."""
        config_id = data['pos.config']['data'][0]['id']
        config = self.env['pos.config'].browse(config_id)
        return [('id', '=', config.select_shortcut_id.id)] if config.select_shortcut_id else [('id', '=', False)]

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Return the fields loaded into the POS session for shortcuts."""
        return ['id', 'customer_screen', 'next_screen', 'select_qty', 'select_discount',
                'select_price', 'delete_orderlines', 'print_receipt', 'next_screen_show',
                'back_screen', 'click_ok', 'select_user', 'select_invoice', 'close_pos',
                'click_cancel', 'validate_order', 'new_order', 'resume_order', 'sent_email']


    @api.model_create_multi
    def create(self, vals_list):
        """Create shortcut records and assign a sequence when needed."""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'pos.keyboard.shortcut')
        return super().create(vals_list)

    @api.constrains('customer_screen', 'next_screen', 'select_qty',
                    'select_discount', 'select_price', 'print_receipt',
                    'back_screen', 'select_user', 'sent_email', 'resume_order',
                    'new_order', 'close_pos', 'select_invoice',
                    'validate_order', 'click_cancel', 'click_ok',
                    'next_screen_show', 'delete_orderlines')
    def _check_same_value(self):
        """Prevent duplicate shortcut keys across the configured fields."""
        for record in self:
            fields_to_check = ['customer_screen', 'next_screen', 'select_qty',
                               'select_discount', 'select_price',
                               'print_receipt', 'back_screen', 'select_user',
                               'sent_email', 'resume_order', 'new_order',
                               'close_pos', 'select_invoice', 'validate_order',
                               'click_cancel', 'next_screen_show',
                               'delete_orderlines']
            field_values = [getattr(record, field) for field in
                            fields_to_check]
            filtered_values = [value for value in field_values if
                               value not in (None, '')]
            if len(set(filtered_values)) != len(filtered_values):
                raise ValidationError(
                    _('The values of the fields must not be the same.'))
