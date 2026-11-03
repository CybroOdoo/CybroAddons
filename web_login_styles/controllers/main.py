# -*- coding: utf-8 -*-
###############################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import hashlib
import logging
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.home import Home as WebHome
from odoo.addons.web.controllers.session import Session

_logger = logging.getLogger(__name__)


class SessionCustom(Session):
    """Custom session controller."""

    @http.route(
        '/web/session/logout',
        type='http',
        auth='none',
        methods=['GET', 'POST'],
        readonly=True,
    )
    def logout(self, redirect='/web/login'):
        return super().logout(redirect=redirect)


class Home(WebHome):
    """Custom web home controller to apply login styles."""

    @http.route()
    def web_login(self, *args, **kw):
        """Extend standard web login to support custom layouts and background
        styles."""
        response = super().web_login(*args, **kw)
        if not getattr(response, 'is_qweb', False):
            return response

        conf_param = request.env['ir.config_parameter'].sudo()
        orientation = conf_param.get_str('web_login_styles.orientation')
        image = conf_param.get_str('web_login_styles.image')
        url = conf_param.get_str('web_login_styles.url')
        background_type = conf_param.get_str('web_login_styles.background')

        if orientation:
            response.qcontext['orientation'] = orientation

        if background_type == 'color':
            response.qcontext['bg'] = ''
            response.qcontext['color'] = conf_param.get_str(
                'web_login_styles.color'
            )
        elif background_type == 'image':
            if image:
                attachments = request.env['ir.attachment'].sudo().search(
                    [('is_background', '=', True)]
                )
                if not attachments:
                    attachment = request.env['ir.attachment'].sudo().create({
                        'name': 'Background Image',
                        'raw': image,
                        'type': 'binary',
                        'public': True,
                        'is_background': True,
                    })
                else:
                    attachment = attachments[0]
                    if len(attachments) > 1:
                        attachments[1:].sudo().unlink()
                    try:
                        current_b64 = (
                            attachment.raw.to_base64()
                            if attachment.raw
                            else ''
                        )
                    except (AttributeError, ValueError):
                        current_b64 = ''
                    if current_b64 != image:
                        attachment.sudo().write({'raw': image})

                img_url = (
                    f'/web/image?model=ir.attachment&id={attachment.id}'
                    f'&field=raw'
                )
                response.qcontext['bg_img'] = img_url
            else:
                response.qcontext['bg_img'] = ''
        elif background_type == 'url':
            attachment = request.env['ir.attachment'].sudo().search(
                [('url', '=', url)], limit=1,
            )
            if not attachment:
                attachment = request.env['ir.attachment'].sudo().create({
                    'name': 'Background Image URL',
                    'url': url,
                    'type': 'url',
                    'public': True,
                })
            encode = hashlib.md5(
                (attachment.url or "").encode("utf-8")
            ).hexdigest()[:7]
            encode_url = f"/web/image/{attachment.id}-{encode}"
            response.qcontext['bg_img'] = encode_url or ''

        if orientation in ('right', 'left', 'middle'):
            response.set_default(
                template=f'web_login_styles.login_template_{orientation}',
                qcontext=response.qcontext,
            )

        return response

