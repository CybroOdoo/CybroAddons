from odoo import models, fields, tools, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    background_image = fields.Binary(string="Background Image", attachment=True)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    theme_background = fields.Binary(string="App menu Background",
                                     related='company_id.background_image',
                                     readonly=False)

    app_bar_color = fields.Char(string='Appbar color',
                                config_parameter='hue_backend_theme.appbar_color',
                                default='#FFFFFF')
    primary_accent = fields.Char(string="Navbar color",
                                 config_parameter='hue_backend_theme.primary_accent_color',
                                 default='#A53860')
    # secondary_accent = fields.Char(string="Navbar color",
    #                                config_parameter='hue_backend_theme.secondary_color',
    #                                default='#0C4D9D')

    kanban_bg_color = fields.Char(string="Kanban Bg Color",
                                  config_parameter='hue_backend_theme.kanban_bg_color',
                                  default='#F7F7F7')

    primary_hover = fields.Char(string="Hover Primary Color",
                                config_parameter='hue_backend_theme.primary_hover',
                                default='#953256')
    light_hover = fields.Char(string="Light Hover",
                              config_parameter='hue_backend_theme.light_hover',
                              default='#d5d5d5')
    appbar_text = fields.Char(string="Home Menu Text Color",
                              config_parameter='hue_backend_theme.appbar_text',
                              default='#F7F8F7')
    secoundary_hover = fields.Char(string="AppBar Hover",
                                   config_parameter='hue_backend_theme.secoundary_hover',
                                   default='#06070f')

    # @api.model
    # def create(self, values):
    #     print("values",values)
        # if 'theme_background' in values:
            # resize_image = tools.image_process(values['theme_background'], (1024, 1024))
            # values['theme_background'] = resize_image
            # return super(ResConfigSettings, self).create(values)

    def config_color_settings(self):
        colors = {}
        colors['full_bg_img'] = self.env.user.company_id.background_image
        colors['appbar_color'] = self.env[
            'ir.config_parameter'].sudo().get_param(
            'hue_backend_theme.appbar_color')
        colors['primary_accent'] = self.env[
            'ir.config_parameter'].sudo().get_param(
            'hue_backend_theme.primary_accent_color')
        colors['secondary_color'] = self.env[
            'ir.config_parameter'].sudo().get_param(
            'hue_backend_theme.secondary_color')
        colors['kanban_bg_color'] = self.env[
            'ir.config_parameter'].sudo().get_param(
            'hue_backend_theme.kanban_bg_color')
        colors['primary_hover'] = self.env[
            'ir.config_parameter'].sudo().get_param(
            'hue_backend_theme.primary_hover')
        colors['light_hover'] = self.env[
            'ir.config_parameter'].sudo().get_param(
            'hue_backend_theme.light_hover')
        colors['appbar_text'] = self.env[
            'ir.config_parameter'].sudo().get_param(
            'hue_backend_theme.appbar_text')
        colors['secoundary_hover'] = self.env[
            'ir.config_parameter'].sudo().get_param(
            'hue_backend_theme.secoundary_hover')

        return colors
