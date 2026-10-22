import { patch } from "@web/core/utils/patch";
import { PosConfig } from "@point_of_sale/app/models/pos_config";
import { GeneratePrinterData } from "@point_of_sale/app/utils/printer/generate_printer_data";
import { imageDataUri } from "@point_of_sale/utils";

patch(PosConfig.prototype, {
    getPosLogoUrl() {
        const rawImage = this.image || this.raw?.image;
        if (rawImage) {
            const raw = typeof rawImage === "object" ? rawImage.content : rawImage;
            if (raw && typeof raw === "string") {
                return raw.startsWith("data:image") ? raw : imageDataUri(raw);
            }
            const configId = this.id || this.raw?.id;
            if (configId) {
                return `/web/image?model=pos.config&field=image&id=${configId}`;
            }
        }
        return false;
    },

    getCompanyLogoUrl() {
        const logo = this.logo || this.raw?.logo;
        if (logo) {
            const raw = typeof logo === "object" ? logo.content : logo;
            if (raw && typeof raw === "string") {
                return raw.startsWith("data:image") ? raw : imageDataUri(raw);
            }
        }
        if (this.company_id?.logo) {
            const raw = typeof this.company_id.logo === "object" ? this.company_id.logo.content : this.company_id.logo;
            if (raw && typeof raw === "string") {
                return raw.startsWith("data:image") ? raw : imageDataUri(raw);
            }
        }
        const companyId = this.company_id?.id || this.company_id || window.odoo?.company_id;
        if (companyId) {
            return `/web/image?model=res.company&field=logo&id=${companyId}`;
        }
        return false;
    },

    get receiptLogoUrl() {
        const option = this.logo_option || this.raw?.logo_option || "pos";
        if (option === "company") {
            return this.getCompanyLogoUrl();
        }
        return this.getPosLogoUrl() || this.getCompanyLogoUrl();
    },
});

function applyLogoDataToReceipt(res, config) {
    if (!res || !config) {
        return res;
    }
    const logoOption = config.logo_option || "pos";
    const posLogo = typeof config.getPosLogoUrl === "function" ? config.getPosLogoUrl() : false;
    const companyLogo = typeof config.getCompanyLogoUrl === "function" ? config.getCompanyLogoUrl() : false;

    res.image = res.image || {};
    res.image.logo_option = logoOption;

    if (logoOption === "pos") {
        res.image.logo = posLogo || companyLogo;
        res.image.pos_logo = false;
        res.image.company_logo = false;
    } else if (logoOption === "company") {
        res.image.logo = companyLogo;
        res.image.pos_logo = false;
        res.image.company_logo = false;
    } else if (logoOption === "both") {
        res.image.pos_logo = posLogo;
        res.image.company_logo = companyLogo;
        res.image.logo = false;
    }
    return res;
}

patch(GeneratePrinterData.prototype, {
    generateReceiptData() {
        const res = super.generateReceiptData(...arguments);
        return applyLogoDataToReceipt(res, this.config);
    },
});
