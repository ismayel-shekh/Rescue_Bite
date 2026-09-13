document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-dismiss]").forEach((element) => {
        element.addEventListener("click", () => element.remove());
    });

    const menuButton = document.querySelector("#mobile-menu-button");
    const mobileMenu = document.querySelector("#mobile-menu");
    if (menuButton && mobileMenu) {
        menuButton.addEventListener("click", () => {
            const open = menuButton.getAttribute("aria-expanded") === "true";
            menuButton.setAttribute("aria-expanded", String(!open));
            mobileMenu.classList.toggle("hidden", open);
            menuButton.setAttribute("aria-label", open ? "Open menu" : "Close menu");
        });
    }

    document.querySelectorAll("[data-workspace-menu-button]").forEach((button) => {
        const sidebar = document.getElementById(button.getAttribute("aria-controls"));
        if (!sidebar) return;
        button.addEventListener("click", () => {
            const open = sidebar.classList.toggle("is-open");
            button.setAttribute("aria-expanded", String(open));
            button.setAttribute("aria-label", open ? "Close workspace menu" : "Open workspace menu");
        });
    });

    const priceInput = document.querySelector("#id_original_price");
    const discountInput = document.querySelector("#id_discount_percentage");
    const discountPreview = document.querySelector("#discount-preview");
    const updateDiscountPreview = () => {
        if (!priceInput || !discountInput || !discountPreview) return;
        const price = Number.parseFloat(priceInput.value);
        const discount = Number.parseFloat(discountInput.value);
        if (!Number.isFinite(price) || !Number.isFinite(discount)) {
            discountPreview.textContent = "Enter an original price and discount to preview the rescue price.";
            return;
        }
        const finalPrice = (price * (1 - discount / 100)).toFixed(2);
        discountPreview.textContent = `Customer price: RM ${finalPrice} (${discount}% off)`;
    };
    priceInput?.addEventListener("input", updateDiscountPreview);
    discountInput?.addEventListener("input", updateDiscountPreview);
    updateDiscountPreview();

    document.querySelectorAll("[data-countdown]").forEach((element) => {
        const deadline = new Date(element.dataset.countdown).getTime();
        const updateCountdown = () => {
            const remaining = deadline - Date.now();
            if (remaining <= 0) {
                element.textContent = "Pickup deadline passed";
                return;
            }
            const totalMinutes = Math.floor(remaining / 60000);
            const hours = Math.floor(totalMinutes / 60);
            const minutes = totalMinutes % 60;
            element.textContent = hours ? `Pickup ends in ${hours}h ${minutes}m` : `Pickup ends in ${minutes}m`;
        };
        updateCountdown();
        window.setInterval(updateCountdown, 30000);
    });
});
