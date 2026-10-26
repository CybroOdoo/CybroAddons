import { Interaction } from "@web/public/interaction";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";

export class SignUpFormExtension extends Interaction {
    static selector = ".oe_signup_form_mobile";
    dynamicContent = {
        ".send-otp-btn": {
            "t-on-click": this._onClickSendOtp,
        },
        'button[type="submit"]': {
            "t-on-click": this._onSubmitClick,
        },
        "#country_code_search": {
            "t-on-input": this._onCountryCodeSearch,
            "t-on-focus": this._onCountryCodeFocus,
        },
        ".country-code-option": {
            "t-on-click": this._onCountryCodeSelect,
        },
        _window: {
            "t-on-click": this._closeDropdown,
        },
    };

    _onCountryCodeFocus() {
        this._showDropdown();
        this.el.querySelectorAll('.country-code-option').forEach(el => {
            el.style.display = '';
        });
    }

    _onCountryCodeSearch() {
        const searchInput = this.el.querySelector('#country_code_search');
        if (!searchInput) return;
        const query = searchInput.value.toLowerCase().replace('+', '').trim();
        const options = this.el.querySelectorAll('.country-code-option');
        options.forEach(el => {
            const name = (el.dataset.name || el.getAttribute('data-name') || '').toLowerCase();
            const code = String(el.dataset.code || el.getAttribute('data-code') || '');
            const matches = name.includes(query) || code.includes(query);
            el.style.display = matches ? '' : 'none';
        });
        this._showDropdown();
    }

    _onCountryCodeSelect(ev) {
        const item = ev.currentTarget;
        const code = item.dataset.code || item.getAttribute('data-code');
        const selectedCodeInput = this.el.querySelector('#selected_country_code');
        const searchInput = this.el.querySelector('#country_code_search');
        if (selectedCodeInput) {
            selectedCodeInput.value = code;
        }
        if (searchInput) {
            searchInput.value = '+' + code;
        }
        this._hideDropdown();
    }

    _showDropdown() {
        const dropdown = this.el.querySelector('#country_code_dropdown');
        if (dropdown) {
            dropdown.style.display = 'block';
        }
    }

    _hideDropdown() {
        const dropdown = this.el.querySelector('#country_code_dropdown');
        if (dropdown) {
            dropdown.style.display = 'none';
        }
    }

    _closeDropdown(ev) {
        const wrapper = this.el.querySelector('.country-code-search-wrapper');
        if (wrapper && !wrapper.contains(ev.target)) {
            this._hideDropdown();
        }
    }

    async _onClickSendOtp(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        const sendOtpBtn = ev.currentTarget;

        const selectedCodeInput = this.el.querySelector('#selected_country_code');
        const searchInput = this.el.querySelector('#country_code_search');
        const countryCode = (selectedCodeInput?.value) ||
            (searchInput ? searchInput.value.replace(/[^0-9]/g, '') : '');
        const mobileInput = this.el.querySelector('#login_mobile') ||
            document.querySelector('.login_mobile');
        const mobile = mobileInput ? mobileInput.value.trim() : '';

        if (!countryCode || !mobile) {
            this.services.notification.add(
                _t("Please enter your country code and mobile number."),
                { type: 'warning' }
            );
            return;
        }

        if (sendOtpBtn) {
            sendOtpBtn.setAttribute('disabled', 'disabled');
            sendOtpBtn.innerText = _t("Sending...");
        }

        try {
            const response = await this.waitFor(rpc('/web/send_otp', {
                country_code: countryCode,
                mobile: mobile,
            }));
            this.services.notification.add(
                response?.message || _t("Verification code sent successfully."),
                { type: 'success' }
            );

            let countdown = 60;
            sendOtpBtn.innerText = `${countdown}s`;
            const timer = setInterval(() => {
                countdown -= 1;
                if (countdown <= 0) {
                    clearInterval(timer);
                    sendOtpBtn.removeAttribute('disabled');
                    sendOtpBtn.innerText = _t("Send OTP");
                } else {
                    sendOtpBtn.innerText = `${countdown}s`;
                }
            }, 1000);
        } catch (error) {
            if (sendOtpBtn) {
                sendOtpBtn.removeAttribute('disabled');
                sendOtpBtn.innerText = _t("Send OTP");
            }
            const errorMsg = error?.data?.message || error?.message ||
                _t("Could not send the verification code. Please try again.");
            this.services.notification.add(errorMsg, { type: 'danger' });
        }
    }

    _onSubmitClick(ev) {
        const selectedCodeInput = this.el.querySelector('#selected_country_code');
        const searchInput = this.el.querySelector('#country_code_search');
        if (selectedCodeInput && !selectedCodeInput.value && searchInput) {
            const searchVal = searchInput.value.replace(/[^0-9]/g, '');
            if (searchVal) {
                selectedCodeInput.value = searchVal;
            }
        }
        const otpInput = this.el.querySelector('#sms_otp_verify');
        if (otpInput && !otpInput.value.trim()) {
            ev.preventDefault();
            this.services.notification.add(
                _t("Please enter the verification code."),
                { type: 'warning' }
            );
        }
    }
}

registry.category("public.interactions").add("signup_with_twilio.signup_form_extension", SignUpFormExtension);
