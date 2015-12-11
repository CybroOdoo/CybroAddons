from openerp import models, fields, tools, api
from openerp.tools.translate import _
from datetime import datetime, timedelta, date
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, image_colorize, image_resize_image_big
import openerp
from openerp.exceptions import Warning


class library_rack(models.Model):
    _name = 'library.rack'
    code = fields.Char(string='Code', size=64, required=True, readonly=True,
                       help="it will be show the position of book")
    name = fields.Char(string='Name', size=16)
    active = fields.Boolean('Active', default=True)
    book_ids = fields.One2many('product.product', compute='compute_book')
    _sql_constraints = [('code.unique', 'unique(code)', 'The code of the rack must be unique !!'),
                        ('name_uniq', 'unique (name)', 'The name of rack already exists !!')]
    _defaults = {'code': lambda self, cr, uid, context: 'rack'}

    def create(self, cr, uid, values, context=None):
        if values.get('code', _('rack')) == _('rack'):
            values['code'] = self.pool.get('ir.sequence').get(cr, uid, 'library.rack')
            return super(library_rack, self).create(cr, uid, values, context=context)

    def compute_book(self):
        book_obj = self.pool.get('product.product')
        browse = self.browse(self._ids)
        student_ids = book_obj.search(self._cr, self._uid, [('rack', '=', browse.name)])
        self.book_ids = student_ids


class product_lang(models.Model):
    _name = 'product.lang'
    code = fields.Char('Code', size=4, required=True, readonly=True)
    name = fields.Char('Name', size=128, required=True)
    book_ids = fields.One2many('product.product', compute='compute_book')
    _sql_constraints = [('name_uniq', 'unique (name)', 'The name of the language must be unique !'),
                        ('code_uniq', 'unique (code)', 'The code of the lang must be unique !')]

    _defaults = {
        'code': lambda self, cr, uid, context: 'language'
    }

    def create(self, cr, uid, values, context=None):
        if values.get('code', _('language')) == _('language'):
            values['code'] = self.pool.get('ir.sequence').get(cr, uid, 'product.lang')
            return super(product_lang, self).create(cr, uid, values, context=context)

    def compute_book(self):
        book_obj = self.pool.get('product.product')
        browse = self.browse(self._ids)
        student_ids = book_obj.search(self._cr, self._uid, [('lang', '=', browse.name)])
        self.book_ids = student_ids


class library_book_returnday(models.Model):
    _name = 'library.book.returnday'
    _rec_name = 'day'
    day = fields.Integer('Days', default=1, required=True, help="It show the no of day/s for returning book")
    code = fields.Char('Code', readonly=True, size=16)
    fine_amt = fields.Float('Fine Amount', default=1, required=True,
                            help="Fine amount to be paid after due of book return date")
    _sql_constraints = [('name_uniq', 'unique (code)', 'The code of the return days must be unique !')]
    _defaults = {'code': lambda self, cr, uid, context: 'day'}

    def create(self, cr, uid, values, context=None):
        if values.get('code', _('day')) == _('day'):
            values['code'] = self.pool.get('ir.sequence').get(cr, uid, 'library.book.returnday')
            return super(library_book_returnday, self).create(cr, uid, values, context=context)


class library_price_category(models.Model):
    _name = 'library.price.category'
    _description = 'Book Category'

    name = fields.Char('Category', size=64, required=True)
    code = fields.Char('Code', readonly=True)
    book_ids = fields.One2many('product.product', compute='compute_book')
    _sql_constraints = [('name_uniq', 'unique (code)', 'The code of the category must be unique !')]
    _defaults = {'code': lambda self, cr, uid, context: 'category'}

    def create(self, cr, uid, values, context=None):
        if values.get('code', _('category')) == _('category'):
            values['code'] = self.pool.get('ir.sequence').get(cr, uid, 'library.price.cat')
            return super(library_price_category, self).create(cr, uid, values, context=context)

    def compute_book(self):
        book_obj = self.pool.get('product.product')
        browse = self.browse(self._ids)
        student_ids = book_obj.search(self._cr, self._uid, [('book_cat', '=', browse.name)])
        self.book_ids = student_ids


class stock_change_quantity(models.Model):
    _inherit = "stock.change.product.qty"

    def change_product_qty(self, cr, uid, ids, context=None):
        conf = self.pool.get('ir.values')
        store_conf = conf.get_default(cr, uid, 'library.config.settings', 'store')
        ware_brow = self.pool.get('stock.warehouse').browse(cr, uid, store_conf, context=context)
        if store_conf == False or store_conf == None:
            raise Warning(_("Warning"), _("Set a store to library from Library settings"))
        get_conf_store = ware_brow.code
        if context is None:
            context = {}
        inventory_obj = self.pool.get('stock.inventory')
        inventory_line_obj = self.pool.get('stock.inventory.line')
        po_id = context.get('active_id')
        prod_obj = self.pool.get('product.product')
        prod = prod_obj.browse(cr, uid, po_id, context=context)
        for data in self.browse(cr, uid, ids, context=context):
            get_trans_loc = data.location_id.location_id.name
            if get_conf_store == get_trans_loc:
                prod_obj.write(cr, uid, po_id, {'total_copies': data.new_quantity,
                                                'available_copies': data.new_quantity})
                if data.new_quantity < 0:
                    raise Warning(_("Warning"), _("Quantity cannot be negative."))
                ctx = context.copy()
                ctx['location'] = data.location_id.id
                ctx['lot_id'] = data.lot_id.id
                if data.product_id.id and data.lot_id.id:
                    filter = 'none'
                elif data.product_id.id:
                    filter = 'product'
                else:
                    filter = 'none'
                inventory_id = inventory_obj.create(cr, uid, {
                    'name': _('INV: %s') % tools.ustr(data.product_id.name),
                    'filter': filter,
                    'product_id': data.product_id.id,
                    'location_id': data.location_id.id,
                    'lot_id': data.lot_id.id}, context=context)
                product = data.product_id.with_context(location=data.location_id.id, lot_id=data.lot_id.id)
                th_qty = product.qty_available
                line_data = {
                    'inventory_id': inventory_id,
                    'product_qty': data.new_quantity,
                    'location_id': data.location_id.id,
                    'product_id': data.product_id.id,
                    'product_uom_id': data.product_id.uom_id.id,
                    'theoretical_qty': th_qty,
                    'prod_lot_id': data.lot_id.id
                }
                inventory_line_obj.create(cr, uid, line_data, context=context)
                inventory_obj.action_done(cr, uid, [inventory_id], context=context)
            return {}


class library_book_issue(models.Model):
    _name = 'library.book.issue'
    _description = "Library information"
    name = fields.Many2one('product.product', 'Book Name', required=True)
    issue_code = fields.Char('Issue No.', size=24, required=True, readonly=True, copy=False)
    user = fields.Many2one('res.partner', 'User Name')
    invoice_id = fields.Many2one('account.invoice', "User's Invoice")
    date_issue = fields.Datetime('Release Date', readonly=True, default=datetime.now(),
                                 help="Release(Issue) date of the book")
    date_return = fields.Datetime(string='Return Date', readonly=True,
                                  help="Book To Be Return On This Date", copy=False)
    actual_return_date = fields.Datetime("Actual Return Date", readonly=True, help="Actual Return Date of Book")
    penalty = fields.Float(string='Penalty For Late Book Return',
                           help='It show the late book return penalty', readonly=True)
    lost_penalty = fields.Float(string='Fine', help='It show the penalty for lost book')
    day_to_return_book = fields.Many2one("library.book.returnday", "Book Return Days", copy=False)
    card_id = fields.Many2one("library.card", "Card No", required=True)
    state = fields.Selection([('draft', 'Draft'), ('issue', 'Issued'), ('transfered', 'Transfered'),
                              ('reissue', 'Reissued'), ('cancel', 'Cancelled'), ('lost', 'Lost'),
                              ('return', 'Returned'), ('paid', 'Paid')], "State")

    color = fields.Integer("Color Index")
    _defaults = {
        'state': 'draft',
        'issue_code': lambda self, cr, uid, context: 'issue'
    }

    def create(self, cr, uid, values, context=None):
        if values.get('issue_code', _('issue')) == _('issue'):
            values['issue_code'] = self.pool.get('ir.sequence').get(cr, uid, 'library.book.issue')
            return super(library_book_issue, self).create(cr, uid, values, context=context)

    @api.multi
    def invoice_print(self):
        return self.env['report'].get_action(self, 'library_management.report_invoice_library')

    def _library_reminder(self, cr, uid, context=None):
        tommarrow = datetime.now() + timedelta(days=1)
        issue_obj = self.pool.get('library.book.issue')
        late_ids = issue_obj.search(cr, uid, [('state', '=', 'transfered')])
        for i in late_ids:
            a = issue_obj.browse(cr, uid, i, context)
            date_return = datetime.strptime(a.date_return, DEFAULT_SERVER_DATETIME_FORMAT)
            if tommarrow.date() == date_return.date():
                post_vars = {'subject': "Library- Reminder",
                             'body': "Hello " + str(a.user.name) + ", Your book(" + str(a.name.name) +
                                     ") return date is tommarrow" + "(" + str(date_return.date()) + ")" +
                                     ". Please try to return the book as soon as possible. Else You need to pay the fine.",
                             'model': 'library.book.issue',
                             'partner_ids': [a.user.id]}
                thread_pool = self.pool.get('mail.thread')
                thread_pool.message_post(cr, uid, False, type="comment", subtype="mt_comment",
                                         context=context, **post_vars)

    def transfer_book(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids):
            conf = self.pool.get('ir.values')
            store_conf = conf.get_default(cr, uid, 'library.config.settings', 'store')
            ware_brow = self.pool.get('stock.warehouse').browse(cr, uid, store_conf, context=context)
            if store_conf == False or store_conf == None:
                raise Warning(_("Warning"), _("Set a store to library from Library settings"))
            product_rec = self.pool.get('product.product').browse(cr, uid, order.name.id, context=context)
            book = product_rec.name
            uom_id = product_rec.uom_id
            searc = self.pool.get('product.product').search(cr, uid, [('product_tmpl_id', '=', book)])
            whstocks = self.pool.get('stock.location').search(cr, uid, [('location_id.name', '=', ware_brow.code),
                                                                        ('name', '=', 'Stock')], context=context)
            whstock = whstocks[0]
            whsto = self.pool.get('stock.location').browse(cr, uid, whstock, context=None)
            search_picks = self.pool.get('stock.picking.type'). \
                search(cr, uid, [('warehouse_id.name', '=', ware_brow.name)], context=context)
            search_pick = search_picks[2]
            picking_vals = {
                'picking_type_id': search_pick,
                'partner_id': order.user.id,
                'date': date.today(),
                'origin': order.issue_code,
            }

            picking_id = self.pool.get('stock.picking').create(cr, uid, picking_vals, context=context)
            vals = {
                'name': order.id or '',
                'product_id': searc[0],
                'product_uom': uom_id.id,
                'date': date.today(),
                'location_id': whsto.id,
                'location_dest_id': order.user.property_stock_customer.id,
                'picking_id': picking_id,
            }
            move_id = self.pool.get('stock.move').create(cr, uid, vals, context=context)
            self.pool.get('stock.move').force_assign(cr, uid, [move_id], context=context)
            return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.picking',
                'context': context,
                'type': 'ir.actions.act_window',
                'res_id': picking_id
            }

    def issue_book(self, cr, uid, ids, context=None):
        product_obj = self.pool.get('product.product')
        for issue in self.browse(cr, uid, ids, context=context):
            card_ids = self.search(cr, uid, [('card_id', '=', issue.card_id.id),
                                             ('state', 'in', ['issue', 'reissue', 'transfered'])])
            if issue.card_id.book_limit > len(card_ids) and issue.name.available_copies > 0:
                self.write(cr, uid, ids, {'state': 'issue', 'date_issue': datetime.now()}, context=context)
            elif issue.card_id.book_limit <= len(card_ids) and issue.name.available_copies > 0:
                raise Warning(_("Warning"), _("Exceeded maximum book limit..."))
            elif issue.card_id.book_limit > len(card_ids) and issue.name.available_copies <= 0:
                raise Warning(_("Warning"), _("Sorry, Currently book not available"))
            elif issue.card_id.book_limit <= len(card_ids) and issue.name.available_copies <= 0:
                raise Warning(_("Warning"), _("Sorry, Currently book not available and Exceeded maximum book limit..."))
            else:
                pass
        return True

    def user_fine(self, cr, uid, ids, context=None):
        conf = self.pool.get('ir.values')
        account_conf = conf.get_default(cr, uid, 'library.config.settings', 'account_id')
        if account_conf == False or account_conf == None:
            raise Warning(_("Warning"), _("Set an account for library from Library settings"))
        lib_account = account_conf
        for i in self.browse(cr, uid, ids):
            state = i.state
            book = i.name.id
            issue_code = i.issue_code

        invoice_obj = self.pool.get('account.invoice')
        obj_data = self.pool.get('ir.model.data')
        pen = 0.0
        fine_per_day = 0.0
        lost_pen = 0.0
        for record in self.browse(cr, uid, ids):
            a = record.date_return
            a = datetime.strptime(a, DEFAULT_SERVER_DATETIME_FORMAT)

            usr = record.user.id
            addr = record.user.contact_address
            user_account = record.user.property_account_receivable.id
            vals_invoice = {
                'partner_id': usr,
                'address_invoice_id': addr,
                'date_invoice': date.today().strftime('%Y-%m-%d'),
                'account_id': user_account,
            }
            invoice_lines = []
            if state == 'lost':
                lost_pen = record.lost_penalty
                invoice_line2 = {
                    'name': issue_code,
                    'price_unit': lost_pen,
                    'product_id': book,
                    'account_id': lib_account
                }
                invoice_lines.append((0, 0, invoice_line2))
            if state != 'lost':
                b = record.actual_return_date
                b = datetime.strptime(b, DEFAULT_SERVER_DATETIME_FORMAT)
                dif = b.date() - a.date()
                day = dif.days

                conf = self.pool.get('ir.values')
                store_conf = conf.get_default(cr, uid, 'library.config.settings', 'fine_per_day')
                fine_amount = store_conf

                if fine_amount < 0.0:
                    raise Warning(_("Warning"),
                                  _("Fine per day must be positive.Set a fine amount from Library settings"))
                fine_per_day += fine_amount * day

                invoicee_obj = self.pool.get('account.invoice.line')
                invoicee_search = invoicee_obj.search(cr, uid, [])
                for i in invoicee_obj.browse(cr, uid, invoicee_search, context=context):
                    if i.name == issue_code:
                        raise Warning(_("Warning"), _("Cannot create two invoice line with same issue code."))
                if a < b:
                    pen = record.penalty + fine_per_day
                    invoice_line1 = {
                        'name': issue_code,
                        'price_unit': pen,
                        'product_id': book,
                        'account_id': lib_account
                    }
                else:
                    invoice_line1 = {
                        'name': issue_code,
                        'price_unit': 0.00,
                        'product_id': book,
                        'account_id': lib_account
                    }

                invoice_lines.append((0, 0, invoice_line1))
        vals_invoice.update({'invoice_line': invoice_lines})
        new_invoice_id = invoice_obj.create(cr, uid, vals_invoice)
        data_id = obj_data._get_id(cr, uid, 'account', 'invoice_form')
        data = obj_data.browse(cr, uid, data_id, context=context)
        view_id = data.res_id
        return {
            'name': _("New Invoice"),
            'view_mode': 'form',
            'view_id': [view_id],
            'view_type': 'form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'res_id': new_invoice_id,
            'target': 'current',
            'context': {}
        }

    def reissue_book(self, cr, uid, ids, context=None):
        new = self.pool.get('library.book.issue').browse(cr, uid, ids, context=context)
        day_to_return_book = new.day_to_return_book.id
        return_days = self.pool.get('library.book.returnday')
        browse = return_days.browse(cr, uid, day_to_return_book, context)
        for item in browse:
            day = item.day
            ret_date = datetime.now() + timedelta(days=day)
        self.write(cr, uid, ids, {'state': 'reissue'}, context=context)
        self.write(cr, uid, ids, {'date_issue': datetime.now(), 'date_return': ret_date}, context=context)
        return True

    def lost_book(self, cr, uid, ids, context=None):
        product_obj = self.pool.get('product.product')
        for issue in self.browse(cr, uid, ids, context=context):
            avail = issue.name.available_copies
            total = issue.name.total_copies - 1
            product_obj.write(cr, uid, issue.name.id, {'total_copies': total}, context=context)
            product_obj.write(cr, uid, issue.name.id, {'available_copies': avail}, context=context)
        self.write(cr, uid, ids, {'state': 'lost'}, context=context)
        return True

    def return_book(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids):
            product_rec = self.pool.get('product.product').browse(cr, uid, order.name.id, context=context)
            book = product_rec.name
            searc = self.pool.get('product.product').search(cr, uid, [('product_tmpl_id', '=', book)])
            conf = self.pool.get('ir.values')
            store_conf = conf.get_default(cr, uid, 'library.config.settings', 'store')
            ware_brow = self.pool.get('stock.warehouse').browse(cr, uid, store_conf, context=context)
            if store_conf == False:
                raise Warning(_("Warning"), _("Set a store to library from Library settings"))
            whstocks = self.pool.get('stock.location'). \
                search(cr, uid, [('location_id.name', '=', ware_brow.code), ('name', '=', 'Stock')], context=context)
            whstock = whstocks[0]
            whsto = self.pool.get('stock.location').browse(cr, uid, whstock, context=None)
            search_picks = self.pool.get('stock.picking.type'). \
                search(cr, uid, [('warehouse_id.name', '=', ware_brow.name)], context=context)
            search_pick = search_picks[0]
            picking_vals = {
                'picking_type_id': search_pick,
                'partner_id': order.user.id,
                'date': date.today(),
                'origin': order.issue_code,
            }
            picking_id = self.pool.get('stock.picking').create(cr, uid, picking_vals, context=context)
            vals = {
                'name': order.id or '',
                'product_id': searc[0],
                'product_uom': product_rec.uom_id.id,
                'date': date.today(),
                'location_id': order.user.property_stock_customer.id,
                'location_dest_id': whsto.id,
                'picking_id': picking_id,

            }
            move_id = self.pool.get('stock.move').create(cr, uid, vals, context=context)
            self.pool.get('stock.move').force_assign(cr, uid, [move_id], context=context)
            return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.picking',
                'context': context,
                'type': 'ir.actions.act_window',
                'res_id': picking_id
            }

    def cancel_book(self, cr, uid, ids, context=None):
        product_obj = self.pool.get('product.product')
        for issue in self.browse(cr, uid, ids, context=context):
            avail = issue.name.available_copies + 1
            product_obj.write(cr, uid, issue.name.id, {'availability': 'available', 'available_copies': avail}, context)
        self.write(cr, uid, ids, {'state': 'cancel'}, context=context)
        return True

    def draft_book(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft'}, context=context)
        return True

    def onchange_card_id(self, cr, uid, ids, card_id, context=None):

        if card_id:
            card_detail = self.pool.get('library.card')
            browse = card_detail.browse(cr, uid, card_id, context)
            for item in browse:
                user = item.username
                return {'value': {'user': user}}

    def on_change_book_name(self, cr, uid, ids, book_name, context=None):
        if book_name:
            fine = 0.0
            for line in self.browse(cr, uid, book_name, context=context):
                book = self.pool.get('product.product')
                bb = book.browse(cr, uid, book_name, context)
                fine = bb.lst_price
            return {'value': {'lost_penalty': fine}}

    def on_change_day_to_return(self, cr, uid, ids, day_to_return_book, context=None):
        if day_to_return_book:
            new = self.pool.get('library.book.issue').browse(cr, uid, ids, context=context)
            datee = new.date_issue
            date = datetime.strptime(str(datee), DEFAULT_SERVER_DATETIME_FORMAT)
            return_days = self.pool.get('library.book.returnday')
            browse = return_days.browse(cr, uid, day_to_return_book, context)
            for item in browse:
                day = item.day
                penalty = item.fine_amt
                ret_date = date + timedelta(days=day)
                self.write(cr, uid, ids, {'date_return': ret_date, 'penalty': penalty}, context)
                return {'value': {'date_return': ret_date, 'penalty': penalty}}


class card_details(models.Model):
    _name = 'library.card'
    name = fields.Char(string='Card No', size=64, required=True)
    username = fields.Many2one('res.partner', "User Name", required=True)
    have_valid_card = fields.Boolean('Have valid Card')
    book_limit = fields.Integer("Book Limit", required=True)
    account_ids = fields.One2many('library.book.issue', compute='compute_account')
    _sql_constraints = [('name_uniq', 'unique (name)', 'The card name must be unique !')]
    _defaults = {'name': lambda self, cr, uid, context: 'card',
                 'have_valid_card': False}

    def copy(self, cr, uid, id, default=None, context=None):
        raise Warning(_('Forbbiden to duplicate'),
                      _('It is not possible to duplicate the record, please create a new one.'))

    def create(self, cr, uid, values, context=None):
        if values.get('name', _('card')) == _('card'):
            values['name'] = self.pool.get('ir.sequence').get(cr, uid, 'library.card')
            return super(card_details, self).create(cr, uid, values, context=context)

    def compute_account(self):
        issue_obj = self.pool.get('library.book.issue')
        browse = self.browse(self._ids)
        student_ids = issue_obj.search(self._cr, self._uid, [('card_id', '=', browse.name)])
        self.account_ids = student_ids

    def onchange_username(self, cr, uid, ids, username, context=None):
        if username:
            card_obj = self.pool.get('library.card')
            card_ids = card_obj.search(cr, uid, [('username', '=', username), ('have_valid_card', '=', True)])
            if len(card_ids) > 0:
                return {'value': {'username': " ", 'user': False, 'book_limit': 0},
                        'warning': {'title': 'Warning', 'message': 'Already the user have a card !'}}

            reg_obj = self.pool.get('library.registration')
            reg_user_draft = reg_obj.search(cr, uid, [('name', '=', username), ('state', '=', 'draft')])
            length_draft = len(reg_user_draft)
            if length_draft > 0:
                return {'value': {'username': " ", 'user': False, 'book_limit': 0},
                        'warning': {'title': 'Warning',
                                    'message': 'Already the user have a registration in draft state!'}}

            reg_user_cancel = reg_obj.search(cr, uid, [('name', '=', username), ('state', '=', 'cancel')])
            length_cancel = len(reg_user_cancel)
            if length_cancel > 0:
                return {'value': {'username': " ", 'user': False, 'book_limit': 0},
                        'warning': {'title': 'Warning',
                                    'message': 'Already the user have a registration in cancel state!'}}
            reg_user_reg = reg_obj.search(cr, uid, [('name', '=', username), ('state', '=', 'registered')])
            length_reg = len(reg_user_reg)
            if length_reg == 0:
                return {'value': {'username': " ", 'user': False, 'book_limit': 0},
                        'warning': {'title': 'Warning',
                                    'message': 'Card not allowed for users without valid registration!'}}


                # def onchange_user(self, cr, uid, ids, user, context=None):
                #   if user:
                #     if user == 'student':
                #         booklimit = 3
                #     if user == 'teacher':
                #         booklimit = 5
                #     if user == 'others':
                #         booklimit = 2
                #     self.write(cr, uid, ids,{'book_limit': booklimit}, context)
                #     return {'value': {'book_limit': booklimit}}


class library_validity(models.Model):
    _name = 'library.validity'
    _rec_name = 'code'
    code = fields.Char('Code', readonly=True, size=16)
    name = fields.Char('Name', readonly=True, default="0 Years, 0 Months, 0 Days", compute='compute_validity')
    year = fields.Integer('Year')
    month = fields.Integer('Month')
    day = fields.Integer('Day')
    _defaults = {'code': lambda self, cr, uid, context: 'Validity'}

    def create(self, cr, uid, values, context=None):
        val_obj = self.search(cr, uid, [])
        for rcd in val_obj:
            val_details = self.browse(cr, uid, rcd, context)
            if val_details.year == values['year'] and val_details.month == values['month'] and val_details.day == \
                    values['day']:
                raise Warning(_("Warning"), _("The record with same validity period already exists."))

        if values.get('code', _('Validity')) == _('Validity'):
            values['code'] = self.pool.get('ir.sequence').get(cr, uid, 'library.validity')
        return super(library_validity, self).create(cr, uid, values, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        year = month = day = 0
        if 'year' in vals:
            year = vals['year']
        if 'month' in vals:
            month = vals['month']
        if 'day' in vals:
            day = vals['day']
        if context is None:
            context = {}
        val_obj = self.search(cr, uid, [])
        for rcd in val_obj:
            val_details = self.browse(cr, uid, rcd, context)
            if val_details.year == year and val_details.month == month and val_details.day == day:
                raise Warning(_("Warning"), _("The record with same validity period already exists."))

        return super(library_validity, self).write(cr, uid, ids, vals, context=context)

    @api.depends('year', 'month', 'day')
    def compute_validity(self):
        year = self.year
        month = self.month
        day = self.day
        validity = str(year) + " Years," + str(month) + " Months," + str(day) + " Days"
        self.name = validity


class res_partner(models.Model):
    _inherit = 'res.partner'
    librarian = fields.Boolean('librarain')
    _defaults = {'librarian': False,
                 }


class library_books(models.Model):
    _inherit = 'product.product'
    book = fields.Boolean('Book')
    editor = fields.Many2one('res.partner', 'Editor', change_default=True)
    author = fields.Many2one('library.author', 'Author', size=30)
    publisher = fields.Many2one('library.publisher', 'Publisher', size=30)
    total_copies = fields.Integer('Total Copies')
    available_copies = fields.Integer('Available Copies')
    book_cat = fields.Many2one('library.price.category', "Book Category")
    availability = fields.Boolean('Available', default=True)
    year_of_publication = fields.Integer('Year of Publication')
    barcode = fields.Char('Barcode')
    rack = fields.Many2one('library.rack', 'Rack', size=16, help="it will be show the position of book")
    isbn = fields.Char('ISBN Code', size=64, unique=True, help="It show the International Standard Book Number")
    lang = fields.Many2one('product.lang', 'Language')
    date_parution = fields.Date('Release date', help="Release(Issue) date of the book")
    creation_date = fields.Datetime('Creation date', readonly=True, help="Record creation date")
    date_retour = fields.Date('Return Date', readonly=True, help='Book Return date')
    nbpage = fields.Integer('Number of pages', size=8)
    back = fields.Selection([('hard', 'Hardback'), ('paper', 'Paperback')], 'Reliure',
                            help="It show the books binding type")
    pocket = fields.Char('Pocket', size=32)
    num_pocket = fields.Char('Collection Num.', size=32, help="It show the collection number in which book is resides")
    num_edition = fields.Integer('Num. edition', help="Edition number of book")
    format = fields.Char('Format', help="The general physical appearance of a book")
    history_ids = fields.One2many('library.book.issue', compute='compute_history')
    _sql_constraints = [

        ('unique_ean13', 'unique(ean13)', 'The ean13 field must be unique across all the products'),
        ('code_uniq', 'unique (code)', 'The code of the product must be unique !')]
    _defaults = {'availability': 'available',
                 }

    def compute_history(self):
        book_obj = self.pool.get('library.book.issue')
        browse = self.browse(self._ids)
        student_ids = book_obj.search(self._cr, self._uid, [('name', '=', browse.name)])
        self.history_ids = student_ids

    def _get_default_image(self, cr, uid, is_company, context=None, colorize=False):
        image_medium = image_colorize(
            open(openerp.modules.get_module_resource('library_management', 'static/src/img', 'book1.png')).read())
        return image_resize_image_big(image_medium.encode('base64'))

    def onchange_total(self, cr, uid, ids, total_copies, context=None):
        prod_obj = self.pool.get('product.product')
        for issue in self.browse(cr, uid, ids, context=context):
            prod_obj.write(cr, uid, issue.id, {'available_copies': total_copies}, context)
        return {'value': {'available_copies': total_copies}}

        # def create(self, cr, uid, values, context=None):
        #     values['book'] = True
        #     return super(library_books, self).create(cr, uid, values, context=context)


class library_author(models.Model):
    _name = 'library.author'
    name = fields.Char('Name', size=30, required=True, select=True)
    code = fields.Char('Code', readonly=True)
    born_date = fields.Date('Date of Birth')
    death_date = fields.Date('Date of Death')
    biography = fields.Text('Biography')
    note = fields.Text('Notes')
    book_ids = fields.One2many('product.product', compute='compute_book')
    _sql_constraints = [('name_uniq', 'unique (name)', 'The name of the author must be unique !'),
                        ('code_uniq', 'unique (code)', 'The code of the collection must be unique !')]
    _defaults = {'code': lambda self, cr, uid, context: 'author'}

    def create(self, cr, uid, values, context=None):
        if values.get('code', _('author')) == _('author'):
            values['code'] = self.pool.get('ir.sequence').get(cr, uid, 'library.author')
            return super(library_author, self).create(cr, uid, values, context=context)

    def unlink(self, cr, uid, ids, context=None):
        author_obj = self.browse(cr, uid, ids)
        book_obj = self.pool.get('product.product')
        search_obj = book_obj.search(cr, uid, [('book', '=', True)])
        for author in author_obj:
            for i in search_obj:
                if book_obj.browse(cr, uid, i).author.name == author.name:
                    raise Warning(_("Warning"), _("Deletion unsuccessful."),
                                  _("Author refered in some records in books."))
        # Call the parent method to eliminate the records.
        super(library_author, self).unlink(cr, uid, ids, context)

    def compute_book(self):
        book_obj = self.pool.get('product.product')
        browse = self.browse(self._ids)
        student_ids = book_obj.search(self._cr, self._uid, [('author', '=', browse.name)])
        self.book_ids = student_ids


class library_publisher(models.Model):
    _name = 'library.publisher'
    name = fields.Char('Name', size=30, required=True)
    code = fields.Char('Code', readonly=True)
    _sql_constraints = [('code_uniq', 'unique (code)', 'The code of the publisher must be unique !')]
    _defaults = {'code': lambda self, cr, uid, context: 'publisher'}

    def create(self, cr, uid, values, context=None):
        if values.get('code', _('publisher')) == _('publisher'):
            values['code'] = self.pool.get('ir.sequence').get(cr, uid, 'library.publisher')
            return super(library_publisher, self).create(cr, uid, values, context=context)


class tranfer_wizard(models.Model):
    _inherit = 'stock.transfer_details'

    @api.one
    def do_detailed_transfer(self, context=None):
        active_id = context.get('active_ids')
        processed_ids = []
        # Create new and update existing pack operations
        for lstits in [self.item_ids, self.packop_ids]:
            for prod in lstits:
                pack_datas = {
                    'product_id': prod.product_id.id,
                    'product_uom_id': prod.product_uom_id.id,
                    'product_qty': prod.quantity,
                    'package_id': prod.package_id.id,
                    'lot_id': prod.lot_id.id,
                    'location_id': prod.sourceloc_id.id,
                    'location_dest_id': prod.destinationloc_id.id,
                    'result_package_id': prod.result_package_id.id,
                    'date': prod.date if prod.date else datetime.now(),
                    'owner_id': prod.owner_id.id,
                }
                if prod.packop_id:
                    prod.packop_id.with_context(no_recompute=True).write(pack_datas)
                    processed_ids.append(prod.packop_id.id)
                else:
                    pack_datas['picking_id'] = self.picking_id.id
                    packop_id = self.env['stock.pack.operation'].create(pack_datas)
                    processed_ids.append(packop_id.id)
        # Delete the others
        packops = self.env['stock.pack.operation'].search(
            ['&', ('picking_id', '=', self.picking_id.id), '!', ('id', 'in', processed_ids)])
        packops.unlink()
        # Execute the transfer of the picking
        self.picking_id.do_transfer()
        issue_code_search = self.pool.get('stock.picking').browse(self._cr, self._uid, active_id)
        for i in issue_code_search:
            issue_code = i.origin
            picking_type = i.picking_type_id.name
        issue_obj = self.pool.get('library.book.issue')
        issue_search = issue_obj.search(self._cr, self._uid, [('issue_code', '=', issue_code)])
        issue_browse = issue_obj.browse(self._cr, self._uid, issue_search)
        product_obj = self.pool.get('product.product')
        if picking_type == 'Receipts':
            for i in issue_browse:
                issue_obj.write(self._cr, self._uid, issue_search,
                                {'state': 'return', 'actual_return_date': datetime.now()})
                avail = i.name.available_copies + 1
                product_obj.write(self._cr, self._uid, i.name.id,
                                  {'availability': 'available', 'available_copies': avail}, context)
        else:
            for i in issue_browse:
                issue_obj.write(self._cr, self._uid, issue_search, {'state': 'transfered'})
                avail = i.name.available_copies - 1
                product_obj.write(self._cr, self._uid, i.name.id, {'available_copies': avail}, context)
        return True


class account_wizard(models.Model):
    _inherit = 'account.voucher'

    def button_proforma_voucher(self, cr, uid, ids, context=None):
        active_id = context.get('active_ids')
        self.pool.get('account.invoice').write(cr, uid, active_id, {'state': 'paid'})
        account_obj = self.pool.get('account.invoice').browse(cr, uid, active_id)
        for i in account_obj.invoice_line:
            issue = i.name
        issue_obj = self.pool.get('library.book.issue')
        issue_search = issue_obj.search(cr, uid, [('issue_code', '=', issue)])
        for i in issue_search:
            issue_obj.write(cr, uid, i, {'state': 'paid'})
        return {'type': 'ir.actions.act_window_close'}
