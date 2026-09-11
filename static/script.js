// ============================================================
// RESOLVE IQ - ENTERPRISE MULTI-PAGE FRONTEND CONTROLLER
// Handles navigation, floating AI chatbot assistant,
// global confirmation modal, toasts, and utilities.
// ============================================================

document.addEventListener("DOMContentLoaded", () => {

    // --------------------------------------------------------
    // 1. MOBILE NAVIGATION DRAWER
    // --------------------------------------------------------
    const mobileMenuBtn = document.getElementById("mobileMenuBtn");
    const sidebar = document.getElementById("sidebar");

    if (mobileMenuBtn && sidebar) {
        mobileMenuBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            sidebar.classList.toggle("mobile-open");
        });

        document.addEventListener("click", (e) => {
            if (
                sidebar.classList.contains("mobile-open") &&
                !sidebar.contains(e.target) &&
                e.target !== mobileMenuBtn
            ) {
                sidebar.classList.remove("mobile-open");
            }
        });

        document.addEventListener("keydown", (e) => {
            if (
                e.key === "Escape" &&
                sidebar.classList.contains("mobile-open")
            ) {
                sidebar.classList.remove("mobile-open");
            }
        });
    }

    // --------------------------------------------------------
    // 2. SMOOTH SCROLL FOR ANCHOR LINKS
    // --------------------------------------------------------
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener("click", function (e) {
            const targetId = this.getAttribute("href");

            if (targetId && targetId !== "#") {
                const targetElement = document.querySelector(targetId);

                if (targetElement) {
                    e.preventDefault();

                    targetElement.scrollIntoView({
                        behavior: "smooth",
                        block: "start"
                    });
                }
            }
        });
    });

    // --------------------------------------------------------
    // 3. GLOBAL STRING ESCAPE UTILITY
    // --------------------------------------------------------
    window.escapeHtml = function (value) {
        if (value === null || value === undefined) {
            return "";
        }

        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    };

    // --------------------------------------------------------
    // 4. GLOBAL TOAST NOTIFICATION SYSTEM
    // --------------------------------------------------------
    const toastContainer = document.getElementById("toastContainer");

    window.showToast = function (
        message,
        type = "info",
        duration = 3500
    ) {
        if (!toastContainer) {
            return;
        }

        const toast = document.createElement("div");
        toast.className = `toast-item toast-${type}`;

        let iconClass = "fa-circle-info";

        if (type === "success") {
            iconClass = "fa-circle-check";
        } else if (
            type === "error" ||
            type === "warning"
        ) {
            iconClass = "fa-triangle-exclamation";
        }

        toast.innerHTML = `
            <i class="fa-solid ${iconClass}"></i>
            <span>${window.escapeHtml(message)}</span>
        `;

        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.transition =
                "opacity 0.3s ease, transform 0.3s ease";

            toast.style.opacity = "0";
            toast.style.transform = "translateX(40px)";

            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);

        }, duration);
    };

    // --------------------------------------------------------
    // 5. GLOBAL CONFIRMATION MODAL
    // --------------------------------------------------------
    const confirmModal =
        document.getElementById("confirmModal");

    const confirmModalTitle =
        document.getElementById("confirmModalTitle");

    const confirmModalMessage =
        document.getElementById("confirmModalMessage");

    const confirmModalCancelBtn =
        document.getElementById("confirmModalCancelBtn");

    const confirmModalCloseBtn =
        document.getElementById("confirmModalCloseBtn");

    const confirmModalConfirmBtn =
        document.getElementById("confirmModalConfirmBtn");

    let currentModalConfirmCallback = null;
    let currentModalCancelCallback = null;

    function hideModal() {
        if (confirmModal) {
            confirmModal.style.display = "none";
        }

        currentModalConfirmCallback = null;
        currentModalCancelCallback = null;
    }

    window.showConfirmModal = function ({
        title = "Confirm Action",
        message = "Are you sure you want to proceed?",
        confirmText = "Confirm",
        confirmClass = "btn-danger",
        onConfirm = null,
        onCancel = null
    } = {}) {

        if (!confirmModal) {
            return;
        }

        if (confirmModalTitle) {
            confirmModalTitle.textContent = title;
        }

        if (confirmModalMessage) {
            confirmModalMessage.textContent = message;
        }

        if (confirmModalConfirmBtn) {
            confirmModalConfirmBtn.textContent = confirmText;

            confirmModalConfirmBtn.className =
                `btn ${confirmClass}`;
        }

        currentModalConfirmCallback = onConfirm;
        currentModalCancelCallback = onCancel;

        confirmModal.style.display = "flex";
    };

    if (confirmModalConfirmBtn) {
        confirmModalConfirmBtn.addEventListener(
            "click",
            () => {
                const cb = currentModalConfirmCallback;

                hideModal();

                if (typeof cb === "function") {
                    cb();
                }
            }
        );
    }

    if (confirmModalCancelBtn) {
        confirmModalCancelBtn.addEventListener(
            "click",
            () => {
                const cb = currentModalCancelCallback;

                hideModal();

                if (typeof cb === "function") {
                    cb();
                }
            }
        );
    }

    if (confirmModalCloseBtn) {
        confirmModalCloseBtn.addEventListener(
            "click",
            () => {
                const cb = currentModalCancelCallback;

                hideModal();

                if (typeof cb === "function") {
                    cb();
                }
            }
        );
    }

    if (confirmModal) {
        confirmModal.addEventListener(
            "click",
            (e) => {
                if (e.target === confirmModal) {
                    hideModal();
                }
            }
        );

        document.addEventListener(
            "keydown",
            (e) => {
                if (
                    e.key === "Escape" &&
                    confirmModal.style.display !== "none"
                ) {
                    hideModal();
                }
            }
        );
    }

    // --------------------------------------------------------
    // 6. FLOATING AI ASSISTANT CHATBOT CONTROLLER
    // --------------------------------------------------------
    const chatLauncherBtn =
        document.getElementById("chatLauncherBtn");

    const sidebarChatTrigger =
        document.getElementById("sidebarChatTrigger");

    const chatDrawer =
        document.getElementById("chatDrawer");

    const closeChatBtn =
        document.getElementById("closeChatBtn");

    const clearChatBtn =
        document.getElementById("clearChatBtn");

    const chatForm =
        document.getElementById("chatForm");

    const chatInput =
        document.getElementById("chatInput");

    const chatMessages =
        document.getElementById("chatMessages");

    const chatSuggestions =
        document.getElementById("chatSuggestions");

    function toggleChatDrawer() {
        if (!chatDrawer) {
            return;
        }

        const isClosed =
            chatDrawer.style.display === "none" ||
            !chatDrawer.style.display;

        chatDrawer.style.display =
            isClosed ? "flex" : "none";

        if (isClosed && chatInput) {
            setTimeout(() => {
                chatInput.focus();
            }, 150);

            scrollChatToBottom();
        }
    }

    if (chatLauncherBtn) {
        chatLauncherBtn.addEventListener(
            "click",
            toggleChatDrawer
        );
    }

    if (sidebarChatTrigger) {
        sidebarChatTrigger.addEventListener(
            "click",
            toggleChatDrawer
        );
    }

    // --------------------------------------------------------
    // URL PARAMETERS
    // --------------------------------------------------------
    let urlParams;

    try {
        urlParams = new URLSearchParams(
            window.location.search
        );
    } catch (e) {
        console.warn(
            "URL query parse error:",
            e
        );

        urlParams = new URLSearchParams();
    }

    // Auto-open chat if requested via query parameter
    if (
        urlParams.get("open_chat") === "1" &&
        chatDrawer
    ) {
        chatDrawer.style.display = "flex";

        if (chatInput) {
            setTimeout(() => {
                chatInput.focus();
            }, 50);
        }
    }

    if (closeChatBtn) {
        closeChatBtn.addEventListener(
            "click",
            () => {
                if (chatDrawer) {
                    chatDrawer.style.display = "none";
                }
            }
        );
    }

    if (clearChatBtn && chatMessages) {
        clearChatBtn.addEventListener(
            "click",
            () => {

                chatMessages.innerHTML = `
                    <div class="chat-msg msg-assistant fade-in">
                        <div class="msg-avatar">
                            <i class="fa-solid fa-robot"></i>
                        </div>

                        <div class="msg-bubble">
                            <p>
                                Conversation reset.
                                How can I assist you with
                                tickets or platform operations today?
                            </p>

                            <small class="msg-time">
                                Just now
                            </small>
                        </div>
                    </div>
                `;
            }
        );
    }

    function scrollChatToBottom() {
        if (chatMessages) {
            chatMessages.scrollTop =
                chatMessages.scrollHeight;
        }
    }

    // --------------------------------------------------------
    // FORMAT CHAT RESPONSE
    // --------------------------------------------------------
    function formatAssistantMessage(text) {

        if (!text) {
            return "";
        }

        let formatted =
            escapeHtml(text);

        // Convert ### headers
        formatted = formatted.replace(
            /^###\s+(.*)$/gm,
            '<strong style="display:block; font-size:13px; color:#ffffff; margin:4px 0 2px 0;">$1</strong>'
        );

        // Convert ## headers
        formatted = formatted.replace(
            /^##\s+(.*)$/gm,
            '<strong style="display:block; font-size:13.5px; color:#ffffff; margin:4px 0 2px 0;">$1</strong>'
        );

        // Convert bold markdown
        formatted = formatted.replace(
            /\*\*(.*?)\*\*/g,
            "<strong>$1</strong>"
        );

        // Convert bullet points
        formatted = formatted.replace(
            /^[\*\-]\s+(.*)$/gm,
            "• $1"
        );

        // Convert newlines
        formatted = formatted.replace(
            /\n/g,
            "<br>"
        );

        // Convert ticket IDs to links
        formatted = formatted.replace(
            /(TKT-[A-Z0-9\-]+)/g,
            '<a href="/ticket/$1" style="color:#29d9ff; font-weight:600; text-decoration:underline;" target="_blank">$1</a>'
        );

        return formatted;
    }

    // --------------------------------------------------------
    // APPEND USER MESSAGE
    // --------------------------------------------------------
    function appendUserMessage(text) {

        if (!chatMessages) {
            return;
        }

        const msgDiv =
            document.createElement("div");

        msgDiv.className =
            "chat-msg msg-user fade-in";

        msgDiv.innerHTML = `
            <div
                class="msg-avatar"
                style="background:rgba(41,217,255,0.2); color:#29d9ff;"
            >
                <i class="fa-solid fa-user"></i>
            </div>

            <div class="msg-bubble">
                <p>${escapeHtml(text)}</p>

                <small class="msg-time">
                    Just now
                </small>
            </div>
        `;

        chatMessages.appendChild(msgDiv);

        scrollChatToBottom();
    }

    // --------------------------------------------------------
    // TYPING INDICATOR
    // --------------------------------------------------------
    function appendTypingIndicator() {

        if (!chatMessages) {
            return null;
        }

        const msgDiv =
            document.createElement("div");

        msgDiv.id =
            "chatTypingIndicator";

        msgDiv.className =
            "chat-msg msg-assistant fade-in";

        msgDiv.innerHTML = `
            <div class="msg-avatar">
                <i class="fa-solid fa-robot"></i>
            </div>

            <div
                class="msg-bubble"
                style="padding:8px 12px;"
            >
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;

        chatMessages.appendChild(msgDiv);

        scrollChatToBottom();

        return msgDiv;
    }

    function removeTypingIndicator() {

        const indicator =
            document.getElementById(
                "chatTypingIndicator"
            );

        if (
            indicator &&
            indicator.parentNode
        ) {
            indicator.parentNode.removeChild(
                indicator
            );
        }
    }

    // --------------------------------------------------------
    // APPEND ASSISTANT MESSAGE
    // --------------------------------------------------------
    function appendAssistantMessage(text) {

        if (!chatMessages) {
            return;
        }

        const msgDiv =
            document.createElement("div");

        msgDiv.className =
            "chat-msg msg-assistant fade-in";

        msgDiv.innerHTML = `
            <div class="msg-avatar">
                <i class="fa-solid fa-robot"></i>
            </div>

            <div class="msg-bubble">
                <p>${formatAssistantMessage(text)}</p>

                <small class="msg-time">
                    Just now
                </small>
            </div>
        `;

        chatMessages.appendChild(msgDiv);

        scrollChatToBottom();
    }

    // --------------------------------------------------------
    // GET CURRENT TICKET ID
    // --------------------------------------------------------
    function getContextTicketId() {

        const path =
            window.location.pathname;

        const match =
            path.match(
                /\/ticket\/([A-Za-z0-9\-]+)/
            );

        if (match && match[1]) {
            return match[1];
        }

        return null;
    }

    // --------------------------------------------------------
    // SEND CHAT MESSAGE
    // --------------------------------------------------------
    async function sendChatMessage(queryText) {

        const trimmed =
            (queryText || "").trim();

        if (!trimmed) {
            return;
        }

        appendUserMessage(trimmed);

        if (chatInput) {
            chatInput.value = "";
        }

        appendTypingIndicator();

        const contextTid =
            getContextTicketId();

        try {

            const res =
                await fetch(
                    "/api/chat",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({
                            message: trimmed,
                            ticket_id: contextTid
                        })
                    }
                );

            const data =
                await res.json();

            removeTypingIndicator();

            if (
                !res.ok ||
                !data.success
            ) {

                appendAssistantMessage(
                    data.error ||
                    "Sorry, I encountered an issue processing your request. Please try again."
                );

                return;
            }

            appendAssistantMessage(
                data.reply ||
                "I have analyzed your query."
            );

        } catch (err) {

            console.error(
                "Chat error:",
                err
            );

            removeTypingIndicator();

            appendAssistantMessage(
                "I'm currently unable to reach the intelligence backend. Please verify your connection."
            );
        }
    }

    // --------------------------------------------------------
    // CHAT FORM
    // --------------------------------------------------------
    if (chatForm) {

        chatForm.addEventListener(
            "submit",
            (e) => {

                e.preventDefault();

                if (chatInput) {
                    sendChatMessage(
                        chatInput.value
                    );
                }
            }
        );
    }

    // --------------------------------------------------------
    // QUICK SUGGESTION PILLS
    // --------------------------------------------------------
    if (chatSuggestions) {

        chatSuggestions
            .querySelectorAll(".sug-pill")
            .forEach(pill => {

                pill.addEventListener(
                    "click",
                    () => {

                        const msg =
                            pill.getAttribute(
                                "data-msg"
                            );

                        if (!msg) {
                            return;
                        }

                        if (
                            chatDrawer &&
                            (
                                chatDrawer.style.display === "none" ||
                                !chatDrawer.style.display
                            )
                        ) {
                            chatDrawer.style.display =
                                "flex";
                        }

                        sendChatMessage(msg);
                    }
                );
            });
    }

    // --------------------------------------------------------
    // AUTO-OPEN CHAT + OPTIONAL QUERY
    // --------------------------------------------------------
    if (
        urlParams.get("open_chat") === "1" &&
        chatDrawer
    ) {

        chatDrawer.style.display =
            "flex";

        scrollChatToBottom();

        const chatQuery =
            urlParams.get("chat_query");

        if (chatQuery) {

            setTimeout(
                () => {
                    sendChatMessage(
                        chatQuery
                    );
                },
                300
            );
        }
    }

    // --------------------------------------------------------
    // 7. ACCOUNT MENU DROPDOWN
    // --------------------------------------------------------
    const accountMenuBtn =
        document.getElementById(
            "accountMenuBtn"
        );

    const accountDropdown =
        document.getElementById(
            "accountDropdown"
        );

    if (
        accountMenuBtn &&
        accountDropdown
    ) {

        accountMenuBtn.addEventListener(
            "click",
            (e) => {

                e.stopPropagation();

                const isOpen =
                    accountDropdown.style.display ===
                    "block";

                accountDropdown.style.display =
                    isOpen
                        ? "none"
                        : "block";
            }
        );

        document.addEventListener(
            "click",
            (e) => {

                if (
                    accountDropdown &&
                    !accountDropdown.contains(e.target) &&
                    !accountMenuBtn.contains(e.target)
                ) {
                    accountDropdown.style.display =
                        "none";
                }
            }
        );

        document.addEventListener(
            "keydown",
            (e) => {

                if (
                    e.key === "Escape" &&
                    accountDropdown
                ) {
                    accountDropdown.style.display =
                        "none";
                }
            }
        );
    }

    // --------------------------------------------------------
    // 8. GLOBAL ROW DROPDOWN TOGGLE HANDLER
    // FOR TICKET QUEUE
    // --------------------------------------------------------
    document.addEventListener(
        "click",
        (e) => {

            // Toggle row dropdown
            const moreBtn =
                e.target.closest(
                    ".btn-icon-more"
                );

            if (moreBtn) {

                e.stopPropagation();

                const container =
                    moreBtn.closest(
                        ".dropdown-container"
                    );

                const menu =
                    container
                        ? container.querySelector(
                            ".row-dropdown-menu"
                        )
                        : null;

                // Close other open menus
                document
                    .querySelectorAll(
                        ".row-dropdown-menu.show"
                    )
                    .forEach(m => {

                        if (m !== menu) {
                            m.classList.remove(
                                "show"
                            );
                        }
                    });

                if (menu) {
                    menu.classList.toggle(
                        "show"
                    );
                }

                return;
            }

            // Close when clicking outside
            if (
                !e.target.closest(
                    ".row-dropdown-menu"
                )
            ) {

                document
                    .querySelectorAll(
                        ".row-dropdown-menu.show"
                    )
                    .forEach(m => {
                        m.classList.remove(
                            "show"
                        );
                    });
            }
        }
    );

    // --------------------------------------------------------
    // INITIALIZATION COMPLETE
    // --------------------------------------------------------
    console.log(
        "✓ Resolve IQ production frontend initialized."
    );

});