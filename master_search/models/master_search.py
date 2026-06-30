# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MasterSearch(models.Model):
    """ Master search model for easy search """
    _name = 'master.search'
    _description = "Model for master search"
    _rec_name = 'name'
    _order = "create_date desc"

    name = fields.Char(string="Name", default=lambda self: _('Search'),
                       help='Searched names')
    search_string = fields.Char(string="Search", help='Details to search')
    search_mode = fields.Selection(
        [('all', 'All'), ('active', 'Active'),
         ('inactive', 'Inactive')],
        string="Search Mode", default="active", help='Search Details based on')
    search_by = fields.Selection(
        [('any', 'Any'), ('customer', 'Customer'),
         ('product', 'Product'),
         ('sale details', 'Sale'),
         ('purchase details', 'Purchase'),
         ('transaction details', 'Inventory'),
         ('account details', 'Accounting')],
        string="Search By", default='any', help='Search in which model')
    master_search_ids = fields.Many2many('master.search',
                                         'master_search_self_rel',
                                         'search_id',
                                         'search_id1',
                                         compute="_get_recent_searches",
                                         help='Recent search details')
    history_count = fields.Integer(string="History Count",
                                   compute="_get_history_count",
                                   help='Recent search History Count')
    customer_ids = fields.Many2many('res.partner',
                                    'master_search_company_rel',
                                    'search_id', 'company_id',
                                    help='To fetch datas of customer search')
    product_ids = fields.Many2many('product.template',
                                   'master_search_product_rel',
                                   'search_id', 'company_id',
                                   help='To fetch datas of product search')
    transaction_ids = fields.Many2many('stock.picking',
                                       'master_search_transaction_rel',
                                       'search_id',
                                       'company_id',
                                       string="Inventory",
                                       help='To fetch datas of inventory'
                                            ' search')
    customer_count = fields.Integer(string="Company Count",
                                    compute="_get_operator_count",
                                    help='To fetched  customer search count')
    product_count = fields.Integer(string="Product Count",
                                   compute="_get_product_count",
                                   help='To fetched  product search count')
    transaction_count = fields.Integer(string="Transaction Count",
                                       compute="_get_transaction_count",
                                       help='To fetched  inventory search '
                                            'count')
    sale_count = fields.Integer(string="Sale Count", compute="_get_sale_count",
                                help='To fetched  sale search count')
    purchase_count = fields.Integer(string="Sale Count",
                                    compute="_get_purchase_count",
                                    help='To fetched  purchase search count')
    account_count = fields.Integer(string="Account Count",
                                   compute="_get_account_count",
                                   help='To fetched  account search count')
    user_id = fields.Many2one('res.users', string="User",
                              default=lambda self: self.env.user)
    match_entire = fields.Boolean(string="Match entire sentence",
                                  help='Only matched datas to be viewed')
    sale_ids = fields.Many2many('sale.order',
                                'master_search_sale_details_rel',
                                'search_id', 'company_id',
                                string="Sale",  help='To fetch datas of sale '
                                                     'search')
    purchase_ids = fields.Many2many('purchase.order',
                                    'master_search_purchase_details_rel',
                                    'search_id', 'company_id',
                                    string="Sale", help='To fetch datas of'
                                                        ' purchase search')
    account_ids = fields.Many2many('account.move',
                                   'master_search_account_details_rel',
                                   'search_id', 'company_id',
                                   string="Account", help='To fetch datas of'
                                                          'account search')

    @api.depends('search_string')
    def _get_recent_searches(self):
        """ Get recent searches """
        try:
            current_id = self.id if isinstance(self.id, int) \
                else self._origin.id
        except:
            current_id = False
            pass
        empty_search = self.env['master.search'].search(
            [('search_string', 'in', ['', False]),
             ('id', 'not in', [current_id, False]
             if current_id else [False])])
        if empty_search:
            empty_search.unlink()
        recent_searches = self.env['master.search'].search([
            ('search_string', 'not in', ['', False])])
        self.master_search_ids = recent_searches

    def action_unlink_search(self):
        """ Unlink search """
        self.unlink()
        action = self.env.ref('master_search.master_search_action').read()[0]
        return action

    @api.depends('master_search_ids')
    def _get_history_count(self):
        """ Get history count """
        self.history_count = len(self.master_search_ids)

    @api.depends('product_ids')
    def _get_product_count(self):
        """ Get product count """
        self.product_count = len(self.product_ids)

    @api.depends('customer_ids')
    def _get_operator_count(self):
        """ Get customer count """
        self.customer_count = len(self.customer_ids)

    @api.depends('transaction_count')
    def _get_transaction_count(self):
        """ Get transaction details count """
        self.transaction_count = len(self.transaction_ids)

    @api.depends('sale_count')
    def _get_sale_count(self):
        """ Get sale details count """
        self.sale_count = len(self.sale_ids)

    @api.depends('purchase_count')
    def _get_purchase_count(self):
        """ Get purchase details count """
        self.purchase_count = len(self.purchase_ids)

    @api.depends('account_count')
    def _get_account_count(self):
        """ Get account details count """
        self.account_count = len(self.account_ids)

    def action_clear_search(self):
        """ clear search input """
        self.search_string = ""
        self.name = "Search"

    @api.model_create_multi
    def create(self, vals_list):
        """ Function for unlink first result and raise error if no string """
        res = super(MasterSearch, self).create(vals_list)
        search_index = self.env['master.search'].search_count(
            [('user_id', '=', self.env.user.id)])
        # unlink old search result if count greater than 10
        if search_index > 10:
            last_search = self.env['master.search'].search(
                [('id', '!=', res.id), ('user_id', '=', self.env.user.id)],
                order="create_date asc", limit=1)
            last_search.unlink() if last_search else False
        return res

    def action_search(self):
        """ search for the string and store search data """
        if self.search_string and "*" in self.search_string:
            return
        if not self.search_string:
            raise UserError(_("Please provide a search string!"))
        search_keys = self.search_string.split(" ")
        self.customer_ids = self.product_ids = self.transaction_ids = False
        self.sale_ids = self.purchase_ids = self.account_ids = False
        if self.match_entire:
            return self._search_query(self.search_string)
        for key in search_keys:
            self._search_query(key)
        self.name = self.search_string

    def _search_query(self, key):
        """ search for the model with given key and update result """
        company_id = self.env.company.id
        self._search_customer(key) \
            if self.search_by in ['any', 'customer'] else False
        self._search_products(key, company_id) \
            if self.search_by in ['any', 'product'] else False
        self._search_inventory_transactions(key, company_id) \
            if self.search_by in ['any', 'transaction details'] else False
        self._search_sale_transactions(key, company_id) \
            if self.search_by in ['any', 'sale details'] else False
        self._search_purchase_transactions(key, company_id) \
            if self.search_by in ['any', 'purchase details'] else False
        self._search_account_transactions(key, company_id) \
            if self.search_by in ['any', 'account details'] else False

    def _get_active_domain(self):
        """ Return active/inactive domain clause based on search_mode """
        if self.search_mode == 'active':
            return [('active', '=', True)]
        elif self.search_mode == 'inactive':
            return [('active', '=', False)]
        # 'all' mode: include both active and inactive
        return ['|', ('active', '=', True), ('active', '=', False)]

    def _search_account_transactions(self, key, company_id):
        """ Search for all account transactions using ORM domain """
        like_key = '%{}%'.format(key)
        domain = [
            ('company_id', '=', company_id),
            '|', '|',
            ('name', 'ilike', like_key),
            ('partner_id.name', 'ilike', like_key),
            ('state', 'ilike', like_key),
        ]
        moves = self.env['account.move'].with_company(company_id).search(domain)
        self.account_ids += moves._filtered_access('read')

    def _search_purchase_transactions(self, key, company_id):
        """ Search for all purchase transactions using ORM domain """
        like_key = '%{}%'.format(key)
        domain = [
            ('company_id', '=', company_id),
            '|', '|',
            ('name', 'ilike', like_key),
            ('partner_id.name', 'ilike', like_key),
            ('state', 'ilike', like_key),
        ]
        purchases = self.env['purchase.order'].with_company(
            company_id).search(domain)
        self.purchase_ids += purchases._filtered_access('read')

    def _search_sale_transactions(self, key, company_id):
        """ Search for all sale transactions using ORM domain """
        like_key = '%{}%'.format(key)
        domain = [
            ('company_id', '=', company_id),
            '|', '|',
            ('name', 'ilike', like_key),
            ('partner_id.name', 'ilike', like_key),
            ('state', 'ilike', like_key),
        ]
        sales = self.env['sale.order'].with_company(company_id).search(domain)
        self.sale_ids += sales._filtered_access('read')

    def _search_inventory_transactions(self, key, company_id):
        """ Search for all inventory transactions using ORM domain """
        like_key = '%{}%'.format(key)
        domain = [
            ('company_id', '=', company_id),
            '|', '|',
            ('name', 'ilike', like_key),
            ('partner_id.name', 'ilike', like_key),
            ('state', 'ilike', like_key),
        ]
        transactions = self.env['stock.picking'].with_company(
            company_id).search(domain)
        self.transaction_ids += transactions._filtered_access('read')

    def _search_products(self, key, company_id):
        """ Search for products using ORM domain """
        like_key = '%{}%'.format(key)
        active_domain = self._get_active_domain()
        domain = active_domain + [
            '|', '|', '|', '|',
            ('name', 'ilike', like_key),
            ('default_code', 'ilike', like_key),
            ('type', 'ilike', like_key),
            ('description', 'ilike', like_key),
            ('categ_id.name', 'ilike', like_key),
        ]
        products = self.env['product.template'].with_company(
            company_id).search(domain)
        self.product_ids += products._filtered_access('read')

    def _search_customer(self, key):
        """ Search for customers using ORM domain """
        like_key = '%{}%'.format(key)
        active_domain = self._get_active_domain()
        domain = active_domain + [
            ('parent_id', '=', False),
            ('type', '=', 'contact'),
            '|', '|', '|', '|', '|',
            ('name', 'ilike', like_key),
            ('street', 'ilike', like_key),
            ('street2', 'ilike', like_key),
            ('city', 'ilike', like_key),
            ('zip', 'ilike', like_key),
            ('email', 'ilike', like_key),
        ]
        customers = self.env['res.partner'].search(domain)
        self.customer_ids += customers._filtered_access('read')
