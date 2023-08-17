import cv2
from pyzbar.pyzbar import decode
from odoo.http import Controller, request
from odoo import http

SIGN_UP_REQUEST_PARAMS = {'db', 'login', 'debug', 'token', 'message', 'error',
                          'scope', 'mode',
                          'redirect', 'redirect_hostname', 'email', 'name',
                          'partner_id',
                          'password', 'confirm_password', 'city', 'country_id',
                          'lang', 'signup_email'}


class LoginController(Controller):
    """controller that works when Login With QR clicked"""

    @http.route(['/web/redirect'], type='http', auth='none', website=True,
                csrf=False, csrf_token=None)
    def open_scanner(self, *args, **kw):
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
                        # Use the overridden web_login method to show error message
                        values = {k: v for k, v in request.params.items() if
                                  k in SIGN_UP_REQUEST_PARAMS}

                        values['error'] = ("Wrong QR Code")
                        request.update_env(user=request.session.uid)
                        request.env["ir.http"]._auth_method_public()
                        response = request.render('web.login', values)

                        return response

                # Display the resulting frame
                cv2.imshow('scanner- to exit press "q"', frame)
                code = cv2.waitKey(1)

                if code == ord('q'):
                    cap.release()
                    cv2.destroyAllWindows()
                    return request.redirect('/web/login')
        except Exception:
            return request.render("login_using_qr.be_patient")

