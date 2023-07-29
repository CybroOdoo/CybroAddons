# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohamed Muzammil VP (odoo@cybrosys.com)
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
###############################################################################
import cv2
from pyzbar.pyzbar import decode
from odoo.http import Controller, request
from odoo import http


class LoginController(Controller):
    """controller that works when Login With QR clicked"""

    @http.route(['/web/redirect'], type='http', auth='none', website=True,
                csrf=False, csrf_token=None)
    def open_scanner(self):
        """This code scan the QR provided and Login to the corresponding user
        note: Only Internal User can login through it"""
        try:
            cap = cv2.VideoCapture(0)
            cap.set(3, 640)
            cap.set(4, 480)

            while True:
                ret, frame = cap.read()
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                for qr_code in decode(gray):
                    (x, y, w, h) = qr_code.rect
                    cv2.rectangle(frame, (x, y), (x + w, y + h),
                                  (0, 255, 0), 2)
                    decoded_text = qr_code.data.decode("utf-8")
                    users = request.env['res.users'].search(
                        [('share', '=', False)])
                    login = users.mapped('login')
                    if decoded_text in login:
                        request.session.authenticate_without_passwd(
                            request.session.db, decoded_text)
                        cap.release()
                        cv2.destroyAllWindows()
                        return request.redirect('/')
                    else:
                        cap.release()
                        cv2.destroyAllWindows()
                        # Rendering the template of redirect
                        return request.render("login_using_qr.redirect_to")

                # Display the resulting frame
                cv2.imshow('scanner- to exit press "q"', frame)
                code = cv2.waitKey(1)

                if code == ord('q'):
                    cap.release()
                    cv2.destroyAllWindows()
                    return request.redirect('/web/login')
        except Exception:
            return request.render("login_using_qr.be_patient")
