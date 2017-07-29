from openerp import models, fields, api, http, SUPERUSER_ID


class MenuThemes(models.Model):
    _name = 'menu.theme'
    _inherit = 'res.config.settings'

    sidebar_image = fields.Binary('Sidebar BackGround Image', help='You can set image at the left bar behind'
                                                                   ' the font such as your company logo.'
                                                                   'keep this field empty '
                                                                   'if you need background colour.')
    top_image = fields.Binary('Top BackGround Image')
    sidebar_font_color = fields.Char('Font Colour of Sidebar Child Menu', default='#FFFFFF')
    sidebar_font_color_parent = fields.Char('Font Colour of Sidebar Parent Menu', default='#FFDC63')
    top_font_color = fields.Char('Font Colour of Top Menu', default='#FFFFFF')
    top_background_color = fields.Char('BackGround Colour of Top Menu', default='#B71E17')
    sidebar_background_color = fields.Char('BackGround Colour of Sidebar', default='#464746')
    font_common = fields.Selection([('sans-serif', 'Sans-Serif'),
                                   ('serif', 'Serif'),
                                   ('monospace', 'Monospace'), ], default='monospace')

    # SETTING
    # FONT STYLE
    def set_font_common(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        wizard = self.browse(cr, uid, ids)[0]
        if wizard.font_common:
            font_common = wizard.font_common
            ir_values.set_default(cr, SUPERUSER_ID, 'menu.theme', 'font_common', font_common)
        else:
            font_common =  False
            ir_values.set_default(cr, SUPERUSER_ID, 'menu.theme', 'font_common', font_common)

    # SIDEBAR BACKGROUND COLOR
    def set_sidebar_background_color(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        wizard = self.browse(cr, uid, ids)[0]
        if wizard.sidebar_background_color:
            sidebar_background_color = wizard.sidebar_background_color
            ir_values.set_default(cr, SUPERUSER_ID, 'menu.theme', 'sidebar_background_color', sidebar_background_color)
        else:
            sidebar_background_color = False
            ir_values.set_default(cr, SUPERUSER_ID, 'menu.theme', 'sidebar_background_color', sidebar_background_color)

    # SIDEBAR IMAGE
    def set_sidebar_image(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        wizard = self.browse(cr, uid, ids)[0]
        if wizard.sidebar_image:
            sidebar_image = wizard.sidebar_image
            ir_values.set_default(cr, SUPERUSER_ID, 'menu.theme', 'sidebar_image', sidebar_image)
        else:
            sidebar_image = False
            ir_values.set_default(cr, SUPERUSER_ID,'menu.theme', 'sidebar_image', sidebar_image)

    # TOP BAR IMAGE
    def set_top_image(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        wizard = self.browse(cr, uid, ids)[0]
        if wizard.top_image:
            top_image = wizard.top_image
            ir_values.set_default(cr, SUPERUSER_ID, 'menu.theme', 'top_image', top_image)
        else:
            top_image = False
            ir_values.set_default(cr, SUPERUSER_ID, 'menu.theme', 'top_image',top_image)

    # FONT COLOUR CHILD
    def set_sidebar_font_color(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        wizard = self.browse(cr, uid, ids)[0]
        if wizard.sidebar_font_color:
            sidebar_font_color = wizard.sidebar_font_color
            ir_values.set_default(cr, SUPERUSER_ID, 'menu.theme', 'sidebar_font_color', sidebar_font_color)
        else:
            sidebar_font_color = False
            ir_values.set_default(cr, SUPERUSER_ID, 'menu.theme', 'sidebar_font_color', sidebar_font_color)

    # FONT COLOUR PARENT
    def set_sidebar_font_color_parent(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        wizard = self.browse(cr, uid, ids)[0]
        if wizard.sidebar_font_color_parent:
            sidebar_font_color_parent = wizard.sidebar_font_color_parent
            ir_values.set_default(cr, SUPERUSER_ID, 'menu.theme', 'sidebar_font_color_parent', sidebar_font_color_parent)
        else:
            sidebar_font_color_parent =  False
            ir_values.set_default(cr, SUPERUSER_ID, 'menu.theme', 'sidebar_font_color_parent', sidebar_font_color_parent)

    # FONT COLOR TOP
    def set_top_font_color(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        wizard = self.browse(cr, uid, ids)[0]
        if wizard.top_font_color:
            top_font_color = wizard.top_font_color
            ir_values.set_default(cr, SUPERUSER_ID, 'menu.theme', 'top_font_color', top_font_color)
        else:
            top_font_color = False
            ir_values.set_default(cr, SUPERUSER_ID, 'menu.theme', 'top_font_color', top_font_color)

    # TOP BAR FONT COLOR
    def set_top_background_color(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        wizard = self.browse(cr, uid, ids)[0]
        if wizard.top_background_color:
            top_background_color = wizard.top_background_color
            ir_values.set_default(cr, SUPERUSER_ID, 'menu.theme', 'top_background_color', top_background_color)
        else:
            top_background_color = False
            ir_values.set_default(cr, SUPERUSER_ID, 'menu.theme', 'top_background_color', top_background_color)

    # GETTING
    # FONT STYLE
    def get_font_common(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        font_common = ir_values.get_default(cr, uid, 'menu.theme', 'font_common')
        return {
            'font_common': font_common, }

    # SIDEBAR BACKGROUND COLOR
    def get_sidebar_background_color(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        sidebar_background_color = ir_values.get_default(cr, uid, 'menu.theme', 'sidebar_background_color')
        return {
            'sidebar_background_color': sidebar_background_color, }

    # SIDEBAR IMAGE
    def get_sidebar_image(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        sidebar_image = ir_values.get_default(cr, uid, 'menu.theme', 'sidebar_image')
        return {
            'sidebar_image': sidebar_image, }

    # TOP BAR IMAGE
    def get_top_image(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        top_image = ir_values.get_default(cr, uid, 'menu.theme', 'top_image')
        return {
            'top_image': top_image, }

    # FONT COLOUR CHILD
    def get_sidebar_font_color(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        sidebar_font_color = ir_values.get_default(cr, uid, 'menu.theme', 'sidebar_font_color')
        return {
            'sidebar_font_color': sidebar_font_color, }

    # FONT COLOUR PARENT
    def get_sidebar_font_color_parent(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        sidebar_font_color_parent = ir_values.get_default(cr, uid, 'menu.theme', 'sidebar_font_color_parent')
        return {
            'sidebar_font_color_parent': sidebar_font_color_parent, }

    # FONT COLOR TOP
    def get_top_font_color(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        top_font_color = ir_values.get_default(cr, uid, 'menu.theme', 'top_font_color')
        return {
            'top_font_color': top_font_color, }

    # TOP BAR FONT COLOR
    def get_top_background_color(self, cr, uid, ids, context=None):
        ir_values = self.pool.get('ir.values')
        top_background_color = ir_values.get_default(cr, uid, 'menu.theme', 'top_background_color')
        return {
            'top_background_color': top_background_color, }

