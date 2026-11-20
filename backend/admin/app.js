(() => {
    const API = "";
    const AUTH_KEY = "itcube_admin_auth";

    const $ = (id) => document.getElementById(id);

    function getAuth() {
        return sessionStorage.getItem(AUTH_KEY);
    }
    function setAuth(login, password) {
        sessionStorage.setItem(AUTH_KEY, "Basic " + btoa(login + ":" + password));
    }
    function clearAuth() {
        sessionStorage.removeItem(AUTH_KEY);
    }

    async function api(path, opts = {}) {
        const headers = opts.headers || {};
        const auth = getAuth();
        if (auth) headers["Authorization"] = auth;
        const resp = await fetch(API + path, { ...opts, headers });
        if (resp.status === 401) {
            clearAuth();
            showLogin();
            throw new Error("Не авторизован");
        }
        if (!resp.ok) {
            let detail = await resp.text();
            try { detail = JSON.parse(detail).detail || detail; } catch (e) {}
            throw new Error(detail || ("HTTP " + resp.status));
        }
        if (resp.status === 204) return null;
        const ct = resp.headers.get("content-type") || "";
        return ct.includes("application/json") ? resp.json() : resp.text();
    }

    function showLogin() {
        $("login-view").classList.remove("hidden");
        $("app-view").classList.add("hidden");
    }
    function showApp() {
        $("login-view").classList.add("hidden");
        $("app-view").classList.remove("hidden");
        const auth = getAuth();
        if (auth) {
            const login = atob(auth.slice(6)).split(":")[0];
            $("who").textContent = login;
        }
    }

    $("login-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const login = $("login-login").value.trim();
        const password = $("login-password").value;
        const err = $("login-error");
        err.textContent = "";
        setAuth(login, password);
        try {
            await api("/admin/items/getall");
            showApp();
            loadItems();
        } catch (e) {
            err.textContent = "Неверный логин или пароль";
        }
    });

    $("logout").addEventListener("click", () => {
        clearAuth();
        $("login-login").value = "";
        $("login-password").value = "";
        showLogin();
    });

    document.querySelectorAll(".tab").forEach((btn) => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
            btn.classList.add("active");
            const tab = btn.dataset.tab;
            document.querySelectorAll(".tab-panel").forEach((p) => p.classList.add("hidden"));
            $("tab-" + tab).classList.remove("hidden");
            if (tab === "items") loadItems();
            if (tab === "claims") loadClaims();
        });
    });

    $("items-refresh").addEventListener("click", loadItems);
    $("items-filter").addEventListener("change", loadItems);
    $("claims-refresh").addEventListener("click", loadClaims);

    function statusLabel(s) {
        return ({
            in_applic: "На модерации",
            accept: "Одобрено",
            not_accept: "Отклонено",
            delete: "Удалено",
            pending: "Ждёт",
            done: "Выдано",
            rejected: "Отклонено",
        })[s] || s;
    }

    async function loadItems() {
        const filter = $("items-filter").value;
        const path = filter === "in_applic"
            ? "/admin/items/getapplic"
            : "/admin/items/getall";
        const list = $("items-list");
        list.innerHTML = "<div class='empty'>Загрузка…</div>";
        try {
            let items = await api(path);
            if (filter !== "all" && filter !== "in_applic") {
                items = items.filter((it) => it.status === filter);
            }
            if (!items.length) {
                list.innerHTML = "<div class='empty'>Пусто</div>";
                return;
            }
            list.innerHTML = "";
            items.forEach((it) => list.appendChild(itemCard(it)));
        } catch (e) {
            list.innerHTML = `<div class='empty'>Ошибка: ${escapeHtml(e.message)}</div>`;
        }
    }

    function itemCard(it) {
        const wrap = document.createElement("div");
        wrap.className = "card";
        wrap.innerHTML = `
            <img class="photo" alt="">
            <div class="body">
                <div class="place"></div>
                <div class="comment"></div>
                <div class="meta">
                    <span class="badge ${it.status}">${statusLabel(it.status)}</span>
                    <span class="muted">#${it.id}</span>
                </div>
            </div>
            <div class="actions"></div>
        `;
        wrap.querySelector(".photo").src = it.url;
        wrap.querySelector(".place").textContent = it.place;
        wrap.querySelector(".comment").textContent = it.comment;
        const actions = wrap.querySelector(".actions");
        const mkBtn = (text, status, cls = "") => {
            const b = document.createElement("button");
            b.textContent = text;
            if (cls) b.className = cls;
            b.addEventListener("click", () => changeItemStatus(it.id, status));
            return b;
        };
        if (it.status === "in_applic") {
            actions.appendChild(mkBtn("Одобрить", "accept"));
            actions.appendChild(mkBtn("Отклонить", "not_accept", "danger"));
        } else if (it.status === "accept") {
            actions.appendChild(mkBtn("Снять с публикации", "in_applic", "ghost"));
            actions.appendChild(mkBtn("Удалить", "delete", "danger"));
        } else if (it.status === "not_accept") {
            actions.appendChild(mkBtn("Вернуть на модерацию", "in_applic", "ghost"));
        } else if (it.status === "delete") {
            actions.appendChild(mkBtn("Восстановить", "in_applic", "ghost"));
        }
        return wrap;
    }

    async function changeItemStatus(id, status) {
        try {
            await api(`/admin/items/${id}/status`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ status }),
            });
            loadItems();
        } catch (e) {
            alert("Ошибка: " + e.message);
        }
    }

    $("add-photo").addEventListener("change", () => {
        const f = $("add-photo").files[0];
        const img = $("add-preview");
        if (!f) { img.hidden = true; img.src = ""; return; }
        img.src = URL.createObjectURL(f);
        img.hidden = false;
    });

    $("add-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const photo = $("add-photo").files[0];
        const place = $("add-place").value.trim();
        const comment = $("add-comment").value.trim();
        const result = $("add-result");
        result.className = "result";
        result.textContent = "";
        if (!photo || !place || !comment) {
            result.textContent = "Заполните все поля";
            result.classList.add("err");
            return;
        }
        try {
            const fd = new FormData();
            fd.append("file", photo);
            const up = await api("/upload", { method: "POST", body: fd });
            await api("/admin/items", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url: up.url, place, comment }),
            });
            result.textContent = "Создано (статус: На модерации)";
            result.classList.add("ok");
            $("add-form").reset();
            $("add-preview").hidden = true;
        } catch (e) {
            result.textContent = "Ошибка: " + e.message;
            result.classList.add("err");
        }
    });

    async function loadClaims() {
        const list = $("claims-list");
        list.innerHTML = "<div class='empty'>Загрузка…</div>";
        try {
            const claims = await api("/admin/claims");
            if (!claims.length) {
                list.innerHTML = "<div class='empty'>Заявок ещё нет</div>";
                return;
            }
            list.innerHTML = "";
            claims.forEach((c) => list.appendChild(claimCard(c)));
        } catch (e) {
            list.innerHTML = `<div class='empty'>Ошибка: ${escapeHtml(e.message)}</div>`;
        }
    }

    function claimCard(c) {
        const wrap = document.createElement("div");
        wrap.className = "card claim-card";
        wrap.innerHTML = `
            <div class="body">
                <div class="meta">
                    <span class="badge ${c.status}">${statusLabel(c.status)}</span>
                    <span class="muted">#${c.id} · ${c.created_at}</span>
                </div>
                <div class="field"><span class="k">Вещь</span><span class="v">#${c.item_id}</span></div>
                <div class="field"><span class="k">ФИО</span><span class="v"></span></div>
                <div class="field"><span class="k">Группа</span><span class="v"></span></div>
                <div class="field"><span class="k">Препод</span><span class="v"></span></div>
            </div>
            <div class="actions"></div>
        `;
        const vals = wrap.querySelectorAll(".field .v");
        vals[1].textContent = c.fio;
        vals[2].textContent = c.group_name;
        vals[3].textContent = c.teacher;
        const actions = wrap.querySelector(".actions");
        const mkBtn = (text, status, cls = "") => {
            const b = document.createElement("button");
            b.textContent = text;
            if (cls) b.className = cls;
            b.addEventListener("click", () => changeClaimStatus(c.id, status));
            return b;
        };
        if (c.status === "pending") {
            actions.appendChild(mkBtn("Выдано", "done"));
            actions.appendChild(mkBtn("Отклонить", "rejected", "danger"));
        } else {
            actions.appendChild(mkBtn("Вернуть в ожидание", "pending", "ghost"));
        }
        return wrap;
    }

    async function changeClaimStatus(id, status) {
        try {
            await api(`/admin/claims/${id}/status`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ status }),
            });
            loadClaims();
        } catch (e) {
            alert("Ошибка: " + e.message);
        }
    }

    function escapeHtml(s) {
        return String(s).replace(/[&<>"']/g, (c) =>
            ({ "&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;" }[c]));
    }

    if (getAuth()) {
        api("/admin/items/getall").then(() => {
            showApp();
            loadItems();
        }).catch(() => showLogin());
    } else {
        showLogin();
    }
})();
