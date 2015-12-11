from openerp import models, fields, api
import openerp
from datetime import datetime,time,date,timedelta
from openerp.tools.translate import _
from openerp.exceptions import Warning
from openerp.tools import image_colorize, image_resize_image_big


class library_registratin(models.Model):
    _name = "library.registration"
    _rec_name = 'name'
    validity = fields.Many2one('library.validity', 'Validity')
    from_id = fields.Date(string='Valid From')
    to = fields.Date(string='Valid To', compute='compute_valid_to')
    notes = fields.Text('Notes')
    photo = fields.Binary('Photo')
    name = fields.Many2one('res.partner', string='Member', size=64, required=True)
    card_no = fields.Char(string='Card No', size=64, readonly=True, help='Unique Card No', copy=False)
    registration_date = fields.Date('Registration Date')
    phone = fields.Char('Phone', size=12)
    mobile = fields.Char('Mobile', size=12)
    state = fields.Selection([('draft', 'Draft'), ('registered', 'Registered'),('assigned_card', 'Card Assigned'), ('cancel', 'Cancel')])
    user = fields.Char("Position")
    book_limit = fields.Integer("Book Limit", required=True)
    _sql_constraints = [('card_no.unique', 'unique(card_no)', 'already existing request id. try another ID')]
    _defaults = {
        'card_no': lambda obj, cr, uid, context: 'Registration no',
        'state': 'draft',
        'photo': lambda self, cr, uid, ctx: self._get_default_image(cr, uid, ctx.get('default_is_company', False), ctx),
    }

    @api.depends('from_id', 'validity')
    def compute_valid_to(self):
        if self.validity:
            days = 0
            if self.validity.year:
                days += self.validity.year*365
            if self.validity.month:
                days += self.validity.month*30
            if self.validity.day:
                days += self.validity.day
            from_id = datetime.strptime(str(self.from_id), '%Y-%m-%d')
            to = from_id + timedelta(days=days)
            self.to = to

    def unlink(self, cr, uid, ids, context=None):
        reg_obj = self.browse(cr, uid, ids)
        issue_obj = self.pool.get('library.book.issue')
        search_obj = issue_obj.search(cr, uid, [])
        for reg in reg_obj:
            for i in search_obj:
                if issue_obj.browse(cr, uid, i).user == reg.name:
                    raise Warning(_("Warning"), _("Deletion unsuccessful."),
                                  _("User have some book issues. Delete those records first!!"))
        super(library_registratin, self).unlink(cr, uid, ids, context)

    def create(self, cr, uid, values, context=None):
        if values.get('card_no', _('Registration no')) == _('Registration no'):
            values['card_no'] = self.pool.get('ir.sequence').get(cr, uid, 'reg.no')
            return super(library_registratin, self).create(cr, uid, values, context=context)

    def _registered_user_manager(self, cr, uid, context=None):
        today = date.today()
        reg_obj = self.pool.get('library.registration')
        late_ids = reg_obj.search(cr, uid, [('to', '<', today)])
        for i in late_ids:
            reg_obj.write(cr, uid, i, {'state': 'cancel'})

    def _get_default_image(self, cr, uid, is_company, context=None, colorize=False):
        image = image_colorize(open(openerp.modules.get_module_resource('base', 'static/src/img', 'avatar.png')).read())
        return image_resize_image_big(image.encode('base64'))

    def getdata(self, cr, uid, ids, name, context=None):
        reg_obj = self.pool.get('library.registration')
        reg_user_registered = reg_obj.search(cr, uid, [('name', '=', name), ('state', '=', 'registered')])
        length_registered = len(reg_user_registered)
        reg_user_assigned_card = reg_obj.search(cr, uid, [('name', '=', name), ('state', '=', 'assigned_card')])
        length_assigned_card = len(reg_user_assigned_card)
        reg_user_cancel = reg_obj.search(cr, uid, [('name', '=', name), ('state', '=', 'cancel')])
        length_cancel = len(reg_user_cancel)
        reg_user_draft = reg_obj.search(cr, uid, [('name', '=', name), ('state', '=', 'draft')])
        length_draft = len(reg_user_draft)
        if length_draft == 1:
                return {'value': {'name': " "}, 'warning': {'title': 'Warning',
                                                            'message': 'User already have a record for registration in draft state'}}
        if length_cancel == 1:
                return {'value': {'name': " "}, 'warning': {'title': 'Warning',
                                                            'message': 'User already have a record for registration in cancel state'}}
        if length_assigned_card == 1 or length_registered == 1:
                return {'value': {'name': " "}, 'warning': {'title': 'Warning',
                                                            'message': 'User already have a record for registration'}}
        obj = self.pool.get('res.partner')
        rec = obj.browse(cr, uid, name, context=None)
        for i in rec:
            return {'value': {'mobile': i.mobile, 'phone': i.phone}}

    def register(self, cr, uid, ids, context=None):
        # flag = 0
        pool_reg = self.pool.get('library.registration')
        pool_partner = self.pool.get('res.partner')
        lib_rec = pool_reg.browse(cr, uid, ids, context=None)
        child_name = lib_rec.name.id
        res_part_browse1 = pool_partner.browse(cr, uid, [child_name], context=None)
        if res_part_browse1.librarian == True:
            raise Warning(_("Warning"), _("Already registered..."))
        else:
            reg_date = date.today()
            a = timedelta(days=365)
            b = reg_date + a
            self.write(cr, uid, ids, {'registration_date': reg_date, 'state': 'registered',
                                      'from_id': reg_date, 'to': b}, context=context)
            res_part_browse1.write({'librarian': True })

    def create_card(self, cr, uid, ids, context=None):
        card_obj = self.pool.get('library.card')
        for i in self.browse(cr, uid, ids):
            username = i.name
            card_ids = card_obj.search(cr, uid, [('id', '=', i.id), ('have_valid_card', '=', True)])
            if len(card_ids) > 0:
                raise Warning(_("Warning"), _("Already the user have a card !"))
            vals = {
                'username': username.id,
                'book_limit': i.book_limit
            }
            new_card_id = card_obj.create(cr, uid, vals)
            self.write(cr, uid, ids, {'state': 'assigned_card'}, context=context)
            obj_data = self.pool.get('ir.model.data')
            data_id = obj_data._get_id(cr, uid, 'library_management', 'product_card_form_view')
            data = obj_data.browse(cr, uid, data_id, context=context)
            view_id = data.res_id
            card_rec = card_obj.browse(cr, uid, new_card_id, context=context)
            card_obj.write(cr, uid, card_rec.id, {'have_valid_card': True}, context=context)
            return {
                'name': _("New card"),
                'view_mode': 'form',
                'view_id': [view_id],
                'view_type': 'form',
                'res_model': 'library.card',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'res_id': new_card_id,
                'target': 'current',
                'context': {}
                }

    def cancel(self, cr, uid, ids, context=None):
        user_issue = self.browse(cr,uid,ids).name.id
        pool_partner = self.pool.get('res.partner')
        res_part_browse1 = pool_partner.browse(cr, uid, user_issue, context=None)
        res_part_browse1.write({'librarian': False })
        card_obj = self.pool.get('library.card')
        card_search = card_obj.search(cr, uid, [('username', '=', user_issue)])
        for i in card_search:
            card_rec = card_obj.browse(cr, uid, i)
            card_obj.write(cr, uid, card_rec.id, {'have_valid_card': False}, context=context)
        # self.unlink(cr, uid, ids, context=context)
        self.write(cr, uid, ids, {'state': 'cancel'}, context=context)
        return True
        # pool_issue = self.pool.get('library.book.issue')
        # pool_card = self.pool.get('library.card')
        # issues = pool_issue.search(cr, uid, [('user', '=', user_issue)])
        # for items in issues:
        #     book = pool_issue.browse(cr, uid, items).issue_code
        #     if pool_issue.browse(cr, uid, items).state =='transfered':
        #         raise Warning(_("Warning"), _("Please return book before cancelling registration"),
        #                        _("Issue no:"), book)
        #     if pool_issue.browse(cr, uid, items).state =='return':
        #         raise Warning(_("Warning"), _("Please pay fine of the returned book before cancelling registration"),
        #                        _("Issue no:"), book)
        #     if pool_issue.browse(cr, uid, items).state =='lost':
        #         raise Warning(_("Warning"), _("Please pay fine of the losted book before cancelling registration"),
        #                        _("Issue no:"), book)
        #     if pool_issue.browse(cr, uid, items).state =='reissue':
        #         raise Warning(_("Warning"), _("Please return the book before cancelling registration"),
        #                        _("Issue no:"), book)
        #     cr.execute('DELETE FROM library_book_issue WHERE id = %s', ([items]))
        # card = pool_card.search(cr, uid, [('username', '=', user_issue)])
        # for i in card:
        #     cr.execute('DELETE FROM library_card WHERE id = %s', ([i]))

    def draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft'}, context=context)
        return True

    def renew(self, cr, uid, ids, context=None):
        reg_date = date.today()
        a = timedelta(days=365)
        b = reg_date + a
        self.write(cr, uid, ids, {'registration_date': reg_date, 'state': 'assigned_card',
                                  'from_id': reg_date, 'to': b}, context=context)


class user_user(models.Model):
    _name = "res.partner"
    _inherit = 'res.partner'
    position = fields.Selection([('student', 'Student'), ('teacher', 'Teacher'), ('other', 'Other')],
                                'Position', required=True)
    reader = fields.Boolean('Reader', help="Check this box if this contact is a reader.", default=True)
    _defaults = {
        'image': lambda self, cr, uid, ctx: self._get_default_image(cr, uid, ctx.get('default_is_company', False), ctx)
    }

    def _get_default_image(self, cr, uid, is_company, context=None, colorize=False):
        image = image_colorize(open(openerp.modules.get_module_resource('base', 'static/src/img', 'avatar.png')).read())
        return image_resize_image_big(image.encode('base64'))


class Wizard(models.TransientModel):
    _name = 'book.report'
    book = fields.Many2one('product.product', "Book")
    rack = fields.Many2one("library.rack", 'Rack')
    author = fields.Many2one("library.author", 'Author')
    language = fields.Many2one('product.lang', 'Language')
    catag = fields.Many2one('library.price.category', "Book category")

    def confirmfilter(self, cr, uid, ids, context=None):
        i = self.browse(cr, uid, ids, context=None)
        book_name = i.book.name
        rack = i.rack.name
        author_name = i.author.name
        lang = i.language.name
        catag = i.catag.name
        dom = [('book', '=', True)]
        if book_name != False:
            dom = [('name', '=', book_name)]
        if rack != False:
            dom.append(('rack', '=', rack))
        if author_name != False:
            dom.append(('author', '=', author_name))
        if lang != False:
            dom.append(('lang', '=', lang))
        if catag != False:
            dom.append(('book_cat', '=', catag))

        return {
            'type': 'ir.actions.act_window',
            'name': 'FILTERED BOOKS',
            'view_type': 'tree',
            'view_mode': 'tree',
            'res_model': 'product.product',
            'target': 'current',
            'domain':  dom
            }

