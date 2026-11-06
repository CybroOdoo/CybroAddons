/** @odoo-module **/

import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

function openModal(modal) {
    if (!modal) return;
    if (modal.parentElement !== document.body) {
        document.body.appendChild(modal);
    }
    modal.style.setProperty("display", "block", "important");
    modal.style.setProperty("z-index", "999999", "important");
    modal.style.setProperty("position", "fixed", "important");
    modal.style.setProperty("left", "0", "important");
    modal.style.setProperty("top", "0", "important");
    modal.style.setProperty("width", "100%", "important");
    modal.style.setProperty("height", "100%", "important");
    modal.style.setProperty("background-color", "rgba(0,0,0,0.6)", "important");
}

function closeModal(modal) {
    if (!modal) return;
    modal.style.setProperty("display", "none", "important");
}

document.addEventListener("click", async (ev) => {
    const btnShowModal = ev.target.closest("#btnShowModal");
    if (btnShowModal) {
        ev.preventDefault();
        ev.stopPropagation();
        const modal = document.querySelector("#myAccountModal");
        openModal(modal);
        return;
    }

    const closeModalBtn = ev.target.closest(".close_modal");
    if (closeModalBtn) {
        ev.preventDefault();
        ev.stopPropagation();
        const modal = document.querySelector("#myAccountModal");
        closeModal(modal);
        return;
    }

    const updateBtn = ev.target.closest("#payment_proof_update");
    if (updateBtn) {
        ev.preventDefault();
        ev.stopPropagation();
        const modal = document.querySelector("#myAccountModal");
        const fileInput = document.querySelector("#my_account_payment_proof");

        if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
            closeModal(modal);
            return;
        }

        const files = Array.from(fileInput.files);
        const filePromises = files.map((file) => {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const dataURL = e.target.result.split(",")[1];
                    resolve({
                        name: file.name,
                        content: dataURL,
                    });
                };
                reader.onerror = reject;
                reader.readAsDataURL(file);
            });
        });

        try {
            const attachments = await Promise.all(filePromises);
            let saleOrderId =
                updateBtn.getAttribute("value") ||
                updateBtn.getAttribute("data-order-id");

            if (!saleOrderId) {
                const showBtn = document.querySelector("#btnShowReceipt");
                if (showBtn) {
                    saleOrderId =
                        showBtn.getAttribute("value") ||
                        showBtn.getAttribute("data-order-id");
                }
            }

            await rpc("/payment_proof/submit", {
                sale_id: saleOrderId ? Number(saleOrderId) : null,
                access_token: updateBtn.dataset.accessToken || null,
                attachments: attachments,
            });

            fileInput.value = "";
            closeModal(modal);

            const showBtn = document.querySelector("#btnShowReceipt");
            if (showBtn) {
                showBtn.click();
            }
        } catch (error) {
            console.error("Error uploading payment proof:", error);
        }
        return;
    }

    const showReceiptBtn =
        ev.target.closest("#btnShowReceipt") ||
        ev.target.closest("#refresh_receipt");
    if (showReceiptBtn) {
        ev.preventDefault();
        ev.stopPropagation();
        const receiptDiv = document.querySelector("#updated_receipt");

        if (receiptDiv) {
            receiptDiv.style.setProperty("display", "block", "important");
        }

        let saleOrderId =
            showReceiptBtn.getAttribute("value") ||
            showReceiptBtn.getAttribute("data-order-id");

        try {
            const attachmentIds = await rpc(
                "/my_account_screen/show_updated",
                {
                    data: String(saleOrderId),
                    access_token: showReceiptBtn.dataset.accessToken || null,
                }
            );

            const showingDiv = document.querySelector("#showing_updated_receipt");
            if (!showingDiv) return;

            showingDiv.innerHTML = "";

            if (attachmentIds && attachmentIds.length > 0) {
                attachmentIds.forEach((attachment) => {
                    const id = attachment.url || `/web/content/${attachment.id}?download=true`;
                    const name = attachment.name;

                    const link = document.createElement("a");
                    link.style.cssText =
                        "width:200px; margin-bottom:5px; " +
                        "overflow:hidden; text-overflow:ellipsis; " +
                        "white-space:nowrap; display:inline-block;";

                    link.className = "btn btn-outline-secondary";
                    link.href = id;
                    link.target = "_blank";
                    link.textContent = `${name} `;
                    const icon = document.createElement("i");
                    icon.className = "fa fa-download";
                    link.appendChild(icon);

                    showingDiv.appendChild(link);
                    showingDiv.appendChild(document.createElement("br"));
                });
            } else {
                const noAttachMsg = document.createElement("p");
                noAttachMsg.style.color = "orange";
                noAttachMsg.textContent =
                    "There are no attachments for this sale order.";

                showingDiv.appendChild(noAttachMsg);
            }
        } catch (error) {
            console.error("Error fetching attachments:", error);
        }
        return;
    }
});

export class MyAccountScreenProof extends Interaction {
    static selector = ".my_account_screen";
}

registry
    .category("public_interactions")
    .add("my_account_screen_proof", MyAccountScreenProof);