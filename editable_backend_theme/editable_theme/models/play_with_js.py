from openerp import api, fields, models, http
from openerp.http import request


class BackendCss(http.Controller):

    @http.route(['/get_css_selected/'], type='json', auth="public", website=True)
    def action_get_css_selected(self):

        sidebar_font_color = request.registry['menu.theme'].get_sidebar_font_color(request.cr, request.uid, []).get('sidebar_font_color')
        sidebar_font_color_parent = request.registry['menu.theme'].get_sidebar_font_color_parent(request.cr, request.uid, []).get('sidebar_font_color_parent')
        sidebar_image = request.registry['menu.theme'].get_sidebar_image(request.cr, request.uid, []).get('sidebar_image')
        top_image = request.registry['menu.theme'].get_top_image(request.cr, request.uid, []).get('top_image')

        top_font_color = request.registry['menu.theme'].get_top_font_color(request.cr, request.uid, []).get('top_font_color')
        top_background_color = request.registry['menu.theme'].get_top_background_color(request.cr, request.uid, []).get('top_background_color')
        sidebar_background_color = request.registry['menu.theme'].get_sidebar_background_color(request.cr, request.uid, []).get('sidebar_background_color')
        font_common = request.registry['menu.theme'].get_font_common(request.cr, request.uid, []).get('font_common')

        css_list = ''
        # SIDE BAR IMAGE
        if sidebar_image:
            css_list += sidebar_image + '-->'
        else:
            css_list += 'none-->'
        # TOP BAR IMAGE
        if top_image:
            css_list += top_image + '-->'
        else:
            css_list += 'none-->'
        # SIDE BAR FONT COLOR CHILD
        if sidebar_font_color:
            css_list += sidebar_font_color + '-->'
        else:
            css_list += 'none-->'
        # SIDE BAR FONT COLOR PARENT
        if sidebar_font_color_parent:
            css_list += sidebar_font_color_parent + '-->'
        else:
            css_list += 'none-->'
        # TOP BAR FONT COLOR
        if top_font_color:
            css_list += top_font_color + '-->'
        else:
            css_list += 'none-->'
        # TOP BAR BACKGROUND COLOR
        if top_background_color:
            css_list += top_background_color + '-->'
        else:
            css_list += 'none-->'
        # SIDE BAR BACKGROUND COLOR
        if sidebar_background_color:
            css_list += sidebar_background_color + '-->'
        else:
            css_list += 'none-->'
        # FONT STYLE
        if font_common:
            css_list += font_common + '-->'
        else:
            css_list += 'none-->'

        return css_list


