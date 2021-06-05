# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#    you can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class MasterSearch(models.Model):
    _name = 'master.search'
    _description = "Model for master search"
    _rec_name = 'name'
    _order = "create_date desc"

    name = fields.Char(string="Name", default=lambda self: _('Search'))
    res_customers_id = fields.Many2many('res.partner', 'res_customers_search_rel', 'res_customers_id', 'search_id',
                                        string="Locations")
    search_string = fields.Char(string="Search")
    search_mode = fields.Selection([('all', 'All'), ('active', 'Active'), ('inactive', 'Inactive')],
                                   string="Search Mode", default="active")
    search_by = fields.Selection(
        [('any', 'Any'), ('customer', 'Customer'), ('product', 'Product'), ('sale details', 'Sale'),
         ('purchase details', 'Purchase'), ('transaction details', 'Inventory'), ('account details', 'Accounting')],
        string="Search By", default='any')
    master_search_ids = fields.Many2many('master.search', 'master_search_self_rel', 'search_id',
                                         'search_id1', compute="_get_recent_searches", limit=1)
    history_count = fields.Integer(string="History Count", compute="_get_history_count")
    customer_ids = fields.Many2many('res.partner', 'master_search_company_rel', 'search_id', 'company_id')
    product_ids = fields.Many2many('product.template', 'master_search_product_rel', 'search_id', 'company_id')
    transaction_details = fields.Many2many('stock.picking', 'master_search_transaction_details_rel', 'search_id',
                                           'company_id', string="Inventory")
    customer_count = fields.Integer(string="Company Count", compute="_get_operator_count")
    product_count = fields.Integer(string="Product Count", compute="_get_product_count")
    transaction_count = fields.Integer(string="Transaction Count", compute="_get_transaction_count")
    sale_count = fields.Integer(string="Sale Count", compute="_get_sale_count")
    purchase_count = fields.Integer(string="Sale Count", compute="_get_purchase_count")
    account_count = fields.Integer(string="Account Count", compute="_get_account_count")
    user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)
    match_entire = fields.Boolean(string="Match entire sentence")
    sale_details = fields.Many2many('sale.order', 'master_search_sale_details_rel', 'search_id',
                                    'company_id', string="Sale")
    purchase_details = fields.Many2many('purchase.order', 'master_search_purchase_details_rel', 'search_id',
                                        'company_id', string="Sale")
    account_details = fields.Many2many('account.move', 'master_search_account_details_rel', 'search_id',
                                       'company_id', string="Account")

    @api.depends('search_string')
    def _get_recent_searches(self):
        """ Get recent searches """
        # unlink search result with empty string
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
        # get search histories avoid null strings
        recent_searches = self.env['master.search'].search([
            ('search_string', 'not in', ['', False])])
        # commended for viewing last search
        # self.master_search_ids = recent_searches.filtered(
        #     lambda x: x.id != self.id) if self.id else recent_searches
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
        self.transaction_count = len(self.transaction_details)

    @api.depends('sale_count')
    def _get_sale_count(self):
        """ Get sale details count """
        self.sale_count = len(self.sale_details)

    @api.depends('purchase_count')
    def _get_purchase_count(self):
        """ Get purchase details count """
        self.purchase_count = len(self.purchase_details)

    @api.depends('account_count')
    def _get_account_count(self):
        """ Get account details count """
        self.account_count = len(self.account_details)

    def action_clear_search(self):
        """ clear search input """
        self.search_string = ""
        self.name = "Search"

    @api.model_create_multi
    def create(self, vals_list):
        """ Function for unlink first result and raise error if no string """
        res = super(MasterSearch, self).create(vals_list)
        search_index = self.env['master.search'].search_count([('user_id', '=', self.env.user.id)])
        # unlink old search result if count greater than 10
        if search_index > 10:
            last_search = self.env['master.search'].search([('id', '!=', res.id), ('user_id', '=', self.env.user.id)],
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
        # delete all the lines
        self.customer_ids = self.product_ids = self.transaction_details = False
        # search for entire sentence
        if self.match_entire:
            return self._search_query(self.search_string)
        # search for all the words
        for key in search_keys:
            self._search_query(key)
        self.name = self.search_string

    def _search_query(self, key):
        """ search for the model with given key and update result """
        company_id = self.env.user.company_id.id
        if self.search_mode == 'all':
            active_qry = """ 
            and obj.active in ({},{})
            """.format("'FALSE'", "'TRUE'")
        elif self.search_mode == 'active':
            active_qry = """ and obj.active in ({})""".format("'TRUE'")
        else:
            active_qry = """ and obj.active in ({})""".format("'FALSE'")

        #  search for customers
        self._search_customer(key, active_qry) \
            if self.search_by in ['any', 'customer'] else False
        # search for products
        self._search_products(key, active_qry, company_id) \
            if self.search_by in ['any', 'product'] else False
        # search for inventory transactions
        self._search_inventory_transactions(key, active_qry, company_id) \
            if self.search_by in ['any', 'transaction details'] else False
        # search for inventory transactions
        self._search_sale_transactions(key, active_qry, company_id) \
            if self.search_by in ['any', 'sale details'] else False
        # search for purchase transactions
        self._search_purchase_transactions(key, active_qry, company_id) \
            if self.search_by in ['any', 'purchase details'] else False
        # search for account transactions
        self._search_account_transactions(key, active_qry, company_id) \
            if self.search_by in ['any', 'account details'] else False

    def _search_account_transactions(self, key, active_qry, company_id):
        """ Search for all account transactions """
        sp_query = """
        SELECT 
            am.id from account_move am
        LEFT JOIN 
            res_partner p on p.id = am.partner_id
        WHERE 
            am.company_id = {op_id}
                AND 
                 (am.name ILIKE '%{key}%'
                OR 
                 p.name ILIKE '%{key}%'
                OR 
                 am.state ILIKE '%{key}%')
        GROUP BY 
            am.id,p.name
        """
        self._cr.execute(sp_query.format(op_id=company_id, key=key, active=active_qry))
        moves = self._cr.dictfetchall()
        move_ids = self.env['account.move'].browse([i['id'] for i in moves])
        self.account_details += move_ids

    def _search_purchase_transactions(self, key, active_qry, company_id):
        """ Search for all purchase transactions """
        sp_query = """
        SELECT 
            po.id from purchase_order po
        LEFT JOIN 
            res_partner p on p.id = po.partner_id
        WHERE 
            po.company_id = {op_id}
                AND 
                 (po.name ILIKE '%{key}%'
                OR 
                 p.name ILIKE '%{key}%'
                OR 
                 po.state ILIKE '%{key}%')
        GROUP BY 
            po.id,p.name
        """
        self._cr.execute(sp_query.format(op_id=company_id, key=key, active=active_qry))
        purchases = self._cr.dictfetchall()
        purchase_ids = self.env['purchase.order'].browse([i['id'] for i in purchases])
        self.purchase_details += purchase_ids

    def _search_sale_transactions(self, key, active_qry, company_id):
        """ Search for all sale transactions """
        sp_query = """
        SELECT 
            sl.id from sale_order sl
        LEFT JOIN 
            res_partner p on p.id = sl.partner_id
        LEFT JOIN 
            product_pricelist pl
                ON 
                 pl.id = sl.pricelist_id
        LEFT JOIN 
            account_payment_term pt
                ON 
                 pt.id = sl.payment_term_id
        WHERE 
            sl.company_id = {op_id}
                AND 
                 (sl.name ILIKE '%{key}%'
                OR 
                 p.name ILIKE '%{key}%'
                OR 
                 sl.state ILIKE '%{key}%'
                OR 
                 pl.name ILIKE '%{key}%')
        GROUP BY 
            sl.id,p.name,pl.name,pt.name
        """
        self._cr.execute(sp_query.format(op_id=company_id, key=key, active=active_qry))
        sales = self._cr.dictfetchall()
        sale_ids = self.env['sale.order'].browse([i['id'] for i in sales])
        self.sale_details += sale_ids

    def _search_inventory_transactions(self, key, active_qry, company_id):
        """ Search for all inventory transactions """
        sp_query = """
        SELECT 
            sp.id from stock_picking sp
        LEFT JOIN 
            res_partner p on p.id = sp.partner_id
        LEFT JOIN 
            stock_picking_type t 
                ON 
                 t.id = sp.picking_type_id
        WHERE 
            sp.company_id = {op_id}
                AND 
                 (sp.name ILIKE '%{key}%'
                OR 
                 p.name ILIKE '%{key}%'
                OR 
                 sp.state ILIKE '%{key}%'
                OR 
                 t.name ILIKE '%{key}%')
        GROUP BY 
            sp.id,p.name,t.name
        """
        self._cr.execute(sp_query.format(op_id=company_id, key=key, active=active_qry))
        transactions = self._cr.dictfetchall()
        transaction_ids = self.env['stock.picking'].browse([i['id'] for i in transactions])
        self.transaction_details += transaction_ids

    def _search_products(self, key, active_qry, company_id):
        """ search for products """
        pt_query = """
        SELECT 
            pt.id 
        FROM 
            product_template pt
        LEFT JOIN 
            product_category pc 
                ON 
                 pc.id = pt.categ_id
        WHERE 
            (pt.name ILIKE '%{key}%'
            OR 
             pt.default_code ILIKE '%{key}%'
            OR 
             pt.type ILIKE '%{key}%'
            OR 
             pt.description ILIKE '%{key}%'
            OR 
             pc.name ILIKE '%{key}%')
    """
        self._cr.execute(pt_query.format(op_id=company_id, key=key, active=active_qry).replace('obj', 'pt'))
        template_ids = self._cr.dictfetchall()
        product_template_ids = self.env['product.template'].browse([i['id'] for i in template_ids])
        self.product_ids += product_template_ids

    def _search_customer(self, key, active_qry):
        """ search for customer """
        query = """ 
        SELECT 
            r.id from res_partner r 
        LEFT JOIN 
            res_country_state rs 
                ON 
                 rs.id = r.state_id
        LEFT JOIN 
            res_country rc 
                ON 
                 rc.id = r.country_id
        WHERE 
            (r.parent_id is NULL ) 
                AND 
                 r.type = 'contact' {active}
                AND 
                 (r.name ILIKE '%{key}%'
                OR 
                 r.street ILIKE '%{key}%'
                OR 
                 r.street2 ILIKE '%{key}%'
                OR 
                 r.city ILIKE '%{key}%'
                OR 
                 r.zip ILIKE '%{key}%'
                OR 
                 rs.name ILIKE '%{key}%'
                OR 
                 rc.name ILIKE '%{key}%'
                OR 
                 r.email ILIKE '%{key}%')
        """
        self._cr.execute(query.format(key=key, active=active_qry).replace('obj', 'r'))
        customers = self._cr.dictfetchall()
        customer_ids = self.env['res.partner'].browse([i['id'] for i in customers])
        self.customer_ids += customer_ids
