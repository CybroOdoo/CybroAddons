/** @odoo-module **/
// Import dependencies
import { rpc } from "@web/core/network/rpc";
/**
 * Handles the behavior of the password hint feature when the "Password Hint" link is clicked.
 */
$('#Password_login_hint').click(function() {
    var self = this;
    var login = $('#login').val();
    if (login) {
        rpc("/website/password/hint", {
            'params': login
        }).then(function(data) {
            if (data) {
                const open_deactivate_modal = true;
                const modalHTML =
                    `<div class="modal ${open_deactivate_modal ? 'show d-block' : ''}" id="popup_error_message" tabindex="-1" role="dialog">
                        <div class="modal-dialog" role="document">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h5 class="modal-title">Password Hint</h5>
                                    <button type="button" class="btn-close" data-dismiss="modal"></button>
                                </div>
                                <form class="oe_login_form modal-body" role="form">
                                    ${data}
                                </form>
                            </div>
                        </div>
                    </div>
                `;
                $("body").append(modalHTML);
                $("body").find("#popup_error_message").find(".btn-close").on("click", function() {
                    $("body").find("#popup_error_message").remove();
                });
            } else {
                const open_deactivate_modal = true;
                const modalHTML =
                    `<div class="modal ${open_deactivate_modal ? 'show d-block' : ''}" id="popup_error_message" tabindex="-1" role="dialog">
                        <div class="modal-dialog" role="document">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h5 class="modal-title">Password Hint</h5>
                                    <button type="button" class="btn-close" data-dismiss="modal"></button>
                                </div>
                                <form class="oe_login_form modal-body" role="form">
                                    No password hint found.
                                </form>
                            </div>
                        </div>
                    </div>
                `;
                $("body").append(modalHTML);
                $("body").find("#popup_error_message").find(".btn-close").on("click", function() {
                    $("body").find("#popup_error_message").remove();
                });
            }
        });
    } else {
        const open_deactivate_modal = true;
        const modalHTML =
            `<div class="modal ${open_deactivate_modal ? 'show d-block' : ''}" id="popup_error_message" tabindex="-1" role="dialog">
                        <div class="modal-dialog" role="document">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <button type="button" class="btn-close" data-dismiss="modal"></button>
                                </div>
                                <form class="oe_login_form modal-body" role="form">
                                    Please enter Email.
                                </form>
                            </div>
                        </div>
                    </div>
                `;
        $("body").append(modalHTML);
        $("body").find("#popup_error_message").find(".btn-close").on("click", function() {
            $("body").find("#popup_error_message").remove();
        });
    }
});
