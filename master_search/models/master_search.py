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
from odoo.exceptions import UserError


class MasterSearch(models.Model):
    """ Master search model for easy search """
    _name = 'master.search'
    _description = "Model for master search"
    _rec_name = 'name'
    _order = "create_date desc"

    name = fields.Char(
        default=lambda self: self.env._('Search'),
        help='Searched names')
    search_string = fields.Char(string="Search", help='Details to search')
    search_mode = fields.Selection(
        [('all', 'All'), ('active', 'Active'),
         ('inactive', 'Inactive')],
        default="active", help='Search Details based on')
    search_by = fields.Selection(
        [('any', 'Any'), ('customer', 'Customer'),
         ('product', 'Product'),
         ('sale details', 'Sale'),
         ('purchase details', 'Purchase'),
         ('transaction details', 'Inventory'),
         ('account details', 'Accounting')],
        default='any', help='Search in which model')
    master_search_ids = fields.Many2many(
        'master.search',
        'master_search_self_rel',
        'search_id',
        'search_id1',
        compute="_compute_recent_searches",
        help='Recent search details')
    history_count = fields.Integer(
        compute="_compute_history_count",
        help='Recent search History Count')
    customer_ids = fields.Many2many(
        'res.partner',
        'master_search_company_rel',
        'search_id', 'company_id',
        help='To fetch data of customer search')
    product_ids = fields.Many2many(
        'product.template',
        'master_search_product_rel',
        'search_id', 'company_id',
        help='To fetch data of product search')
    transaction_ids = fields.Many2many(
        'stock.picking',
        'master_search_transaction_rel',
        'search_id',
        'company_id',
        string="Inventory",
        help='To fetch data of inventory search')
    customer_count = fields.Integer(
        compute="_compute_customer_count",
        help='To fetch customer search count')
    product_count = fields.Integer(
        compute="_compute_product_count",
        help='To fetch product search count')
    transaction_count = fields.Integer(
        compute="_compute_transaction_count",
        help='To fetch inventory search count')
    sale_count = fields.Integer(
        compute="_compute_sale_count",
        help='To fetch sale search count')
    purchase_count = fields.Integer(
        compute="_compute_purchase_count",
        help='To fetch purchase search count')
    account_count = fields.Integer(
        compute="_compute_account_count",
        help='To fetch account search count')
    user_id = fields.Many2one(
        'res.users',
        default=lambda self: self.env.user)
    match_entire = fields.Boolean(
        help='Only matched records to be displayed')
    sale_ids = fields.Many2many(
        'sale.order',
        'master_search_sale_details_rel',
        'search_id', 'company_id',
        help='To fetch data of sale search')
    purchase_ids = fields.Many2many(
        'purchase.order',
        'master_search_purchase_details_rel',
        'search_id', 'company_id',
        help='To fetch data of purchase search')
    account_ids = fields.Many2many(
        'account.move',
        'master_search_account_details_rel',
        'search_id', 'company_id',
        help='To fetch data of account search')

    @api.depends('search_string')
    def _compute_recent_searches(self):
        """ Get recent searches """
        for rec in self:
            recent_searches = rec.env['master.search'].search([
                ('search_string', 'not in', ['', False]),
                ('user_id', '=', self.env.user.id),
            ], order='create_date desc', limit=10)
            rec.master_search_ids = recent_searches

    def action_unlink_search(self):
        """ Unlink search """
        self.unlink()
        return self.env['ir.actions.act_window']._for_xml_id('master_search.master_search_action')

    @api.depends('master_search_ids')
    def _compute_history_count(self):
        """ Get history count """
        for rec in self:
            rec.history_count = len(rec.master_search_ids)

    @api.depends('product_ids')
    def _compute_product_count(self):
        """ Get product count """
        for rec in self:
            rec.product_count = len(rec.with_context(active_test=False).product_ids)

    @api.depends('customer_ids')
    def _compute_customer_count(self):
        """ Get customer count """
        for rec in self:
            rec.customer_count = len(rec.with_context(active_test=False).customer_ids)

    @api.depends('transaction_ids')
    def _compute_transaction_count(self):
        """ Get transaction details count """
        for rec in self:
            rec.transaction_count = len(rec.transaction_ids)

    @api.depends('sale_ids')
    def _compute_sale_count(self):
        """ Get sale details count """
        for rec in self:
            rec.sale_count = len(rec.sale_ids)

    @api.depends('purchase_ids')
    def _compute_purchase_count(self):
        """ Get purchase details count """
        for rec in self:
            rec.purchase_count = len(rec.purchase_ids)

    @api.depends('account_ids')
    def _compute_account_count(self):
        """ Get account details count """
        for rec in self:
            rec.account_count = len(rec.account_ids)

    def action_clear_search(self):
        """ clear search input """
        self.search_string = ""
        self.name = "Search"

    @api.model_create_multi
    def create(self, vals_list):
        """ Function for unlink first result and raise error if no string """
        res = super().create(vals_list)
        search_index = self.env['master.search'].search_count(
            [('user_id', '=', self.env.user.id)])
        # unlink old search result if count greater than 10
        if search_index > 10:
            last_search = self.env['master.search'].search(
                [('id', '!=', res.id), ('user_id', '=', self.env.user.id)],
                order="create_date asc", limit=1)
            if last_search:
                last_search.unlink()
        return res

    def action_search(self):
        """ search for the string and store search data """
        if self.search_string and "*" in self.search_string:
            return
        if not self.search_string:
            raise UserError(self.env._("Please provide a search string!"))
        search_keys = self.search_string.split(" ")
        self.customer_ids = self.product_ids = self.transaction_ids = False
        self.sale_ids = self.purchase_ids = self.account_ids = False
        if self.match_entire:
            self._search_query(self.search_string)
        else:
            for key in search_keys:
                self._search_query(key)
        self.name = self.search_string

    def _search_query(self, key):
        """ search for the model with given key and update result """
        company_id = self.env.company.id
        if self.search_mode == 'all':
            active_vals = [True, False]
        elif self.search_mode == 'active':
            active_vals = [True]
        else:
            active_vals = [False]
        if self.search_by in ['any', 'customer']:
            self._search_customer(key, active_vals, company_id)
        if self.search_by in ['any', 'product']:
            self._search_products(key, active_vals, company_id)
        if self.search_by in ['any', 'transaction details']:
            self._search_inventory_transactions(key, active_vals, company_id)
        if self.search_by in ['any', 'sale details']:
            self._search_sale_transactions(key, active_vals, company_id)
        if self.search_by in ['any', 'purchase details']:
            self._search_purchase_transactions(key, active_vals, company_id)
        if self.search_by in ['any', 'account details']:
            self._search_account_transactions(key, active_vals, company_id)

    @api.model
    def _get_active_params(self, active_vals):
        """Helper to get list of active booleans and allow_null flag."""
        if isinstance(active_vals, (list, tuple, set)):
            vals = list(active_vals)
        elif isinstance(active_vals, str) and 'FALSE' in active_vals and 'TRUE' in active_vals:
            vals = [True, False]
        elif isinstance(active_vals, str) and 'FALSE' in active_vals:
            vals = [False]
        else:
            vals = [True]
        allow_null = True in vals
        return vals, allow_null

    def _search_account_transactions(self, key, active_vals, company_id):
        """ Search for all account transactions """
        search_value = f'%{key}%'
        vals, allow_null = self._get_active_params(active_vals)
        sp_query = """
            SELECT DISTINCT am.id FROM account_move am
            LEFT JOIN res_partner p ON p.id = am.partner_id
            WHERE am.company_id = %s
              AND (p.active = ANY(%s) OR (p.id IS NULL AND %s))
              AND (
                  am.name ILIKE %s
               OR p.name ILIKE %s
               OR am.state ILIKE %s
              )
        """
        self.env.cr.execute(
            sp_query,
            (company_id, vals, allow_null, search_value, search_value, search_value),
        )
        moves = self.env.cr.dictfetchall()
        move_ids = self.env['account.move'].browse([i['id'] for i in moves])
        self.account_ids += move_ids._filtered_access('read')

    def _search_purchase_transactions(self, key, active_vals, company_id):
        """ Search for all purchase transactions """
        search_value = f'%{key}%'
        vals, allow_null = self._get_active_params(active_vals)
        sp_query = """
            SELECT DISTINCT po.id FROM purchase_order po
            LEFT JOIN res_partner p ON p.id = po.partner_id
            WHERE po.company_id = %s
              AND (p.active = ANY(%s) OR (p.id IS NULL AND %s))
              AND (
                  po.name ILIKE %s
               OR p.name ILIKE %s
               OR po.state ILIKE %s
              )
        """
        self.env.cr.execute(
            sp_query,
            (company_id, vals, allow_null, search_value, search_value, search_value),
        )
        purchases = self.env.cr.dictfetchall()
        purchase_ids = self.env['purchase.order'].browse(
            [i['id'] for i in purchases])
        self.purchase_ids += purchase_ids._filtered_access('read')

    def _search_sale_transactions(self, key, active_vals, company_id):
        """ Search for all sale transactions """
        search_value = f'%{key}%'
        vals, allow_null = self._get_active_params(active_vals)
        sp_query = """
            SELECT DISTINCT sl.id FROM sale_order sl
            LEFT JOIN res_partner p ON p.id = sl.partner_id
            LEFT JOIN product_pricelist pl ON pl.id = sl.pricelist_id
            LEFT JOIN account_payment_term pt ON pt.id = sl.payment_term_id
            WHERE sl.company_id = %s
              AND (p.active = ANY(%s) OR (p.id IS NULL AND %s))
              AND (
                  sl.name ILIKE %s
               OR p.name ILIKE %s
               OR sl.state ILIKE %s
               OR pl.name::text ILIKE %s
              )
        """
        self.env.cr.execute(
            sp_query,
            (company_id, vals, allow_null, search_value, search_value, search_value, search_value),
        )
        sales = self.env.cr.dictfetchall()
        sale_ids = self.env['sale.order'].browse([i['id'] for i in sales])
        self.sale_ids += sale_ids._filtered_access('read')

    def _search_inventory_transactions(self, key, active_vals, company_id):
        """ Search for all inventory transactions """
        search_value = f'%{key}%'
        vals, allow_null = self._get_active_params(active_vals)
        sp_query = """
            SELECT DISTINCT sp.id FROM stock_picking sp
            LEFT JOIN res_partner p ON p.id = sp.partner_id
            LEFT JOIN stock_picking_type t ON t.id = sp.picking_type_id
            WHERE sp.company_id = %s
              AND (p.active = ANY(%s) OR (p.id IS NULL AND %s))
              AND (
                  sp.name ILIKE %s
               OR p.name ILIKE %s
               OR sp.state ILIKE %s
               OR t.name::text ILIKE %s
              )
        """
        self.env.cr.execute(
            sp_query,
            (company_id, vals, allow_null, search_value, search_value, search_value, search_value),
        )
        transactions = self.env.cr.dictfetchall()
        transaction_ids = self.env['stock.picking'].browse(
            [i['id'] for i in transactions])
        self.transaction_ids += transaction_ids._filtered_access('read')

    def _search_products(self, key, active_vals, company_id):
        """ search for products """
        language = self.env.lang or 'en_US'
        search_value = f'%{key}%'
        vals, _allow_null = self._get_active_params(active_vals)

        pt_query = """
                SELECT DISTINCT pt.id
                  FROM product_template AS pt
             LEFT JOIN product_category AS pc ON pc.id = pt.categ_id
                 WHERE pt.active = ANY(%s)
                   AND (pt.company_id IS NULL OR pt.company_id = %s)
                   AND (
                        COALESCE(pt.name->>%s, '') ILIKE %s
                     OR COALESCE(pt.default_code, '') ILIKE %s
                     OR COALESCE(pt.type::text, '') ILIKE %s
                     OR COALESCE(pt.description->>%s, '') ILIKE %s
                     OR COALESCE(pc.name->>%s, '') ILIKE %s
                 )
            """
        self.env.cr.execute(
            pt_query,
            (
                vals,
                company_id,
                language, search_value,
                search_value,
                search_value,
                language, search_value,
                language, search_value,
            ),
        )
        template_ids = self.env.cr.dictfetchall()
        product_template_ids = self.env['product.template'].browse(
            [i['id'] for i in template_ids])
        self.product_ids += product_template_ids._filtered_access('read')

    def _search_customer(self, key, active_vals, company_id):
        """ search for customer """
        search_value = f'%{key}%'
        vals, _allow_null = self._get_active_params(active_vals)

        query = """
            SELECT DISTINCT r.id FROM res_partner r
            WHERE (r.parent_id IS NULL)
              AND r.type = 'contact'
              AND r.active = ANY(%s)
              AND (r.company_id IS NULL OR r.company_id = %s)
              AND (
                  r.name ILIKE %s
               OR r.street ILIKE %s
               OR r.street2 ILIKE %s
               OR r.city ILIKE %s
               OR r.zip ILIKE %s
               OR r.email ILIKE %s
              )
        """
        self.env.cr.execute(
            query,
            (
                vals,
                company_id,
                search_value,
                search_value,
                search_value,
                search_value,
                search_value,
                search_value,
            ),
        )
        customers = self.env.cr.dictfetchall()
        customer_ids = self.env['res.partner'].browse(
            [i['id'] for i in customers])
        self.customer_ids += customer_ids._filtered_access('read')
