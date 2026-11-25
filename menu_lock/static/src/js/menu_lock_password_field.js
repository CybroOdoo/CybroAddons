import { registry } from "@web/core/registry";
import { CharField, charField } from "@web/views/fields/char/char_field";

class MenuLockPasswordField extends CharField {
    get formattedValue() {
        const { has_password, password_length } = this.props.record.data;
        return has_password ? "*".repeat(password_length || 1) : super.formattedValue;
    }
}

registry.category("fields").add("menu_lock_password", {
    ...charField,
    component: MenuLockPasswordField,
    supportedTypes: ["char"],
});
