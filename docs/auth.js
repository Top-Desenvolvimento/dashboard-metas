import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm";

const SUPABASE_URL = "https://iahdagpmejyjspkktriw.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlhaGRhZ3BtZWp5aXNwa2t0cml3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NDUxMTEzNiwiZXhwIjoyMDkwMDg3MTM2fQ.ZOrfKiZaT8EzNOmAG_u-2jabVWTK6jm5F3JP8cdWhdA";

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

const style = document.createElement("style");
style.textContent = `
  html.auth-loading,
  body.auth-loading {
    overflow: hidden !important;
  }

  body.auth-locked > *:not(#auth-overlay):not(#auth-userbar) {
    visibility: hidden !important;
    pointer-events: none !important;
    user-select: none !important;
  }

  #auth-overlay {
    position: fixed;
    inset: 0;
    z-index: 999999;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
    background:
      radial-gradient(circle at top left, rgba(0,232,255,.08), transparent 30%),
      radial-gradient(circle at top right, rgba(18,217,159,.06), transparent 24%),
      linear-gradient(180deg, #030912, #06111c 45%, #030912 100%);
    font-family: Inter, Arial, sans-serif;
  }

  #auth-overlay.hidden {
    display: none !important;
  }

  .auth-card {
    width: 100%;
    max-width: 430px;
    background: linear-gradient(180deg, rgba(13,31,49,.98), rgba(10,24,40,.96));
    border: 1px solid rgba(0, 232, 255, 0.12);
    border-radius: 22px;
    box-shadow: 0 0 0 1px rgba(0,232,255,.05), 0 14px 28px rgba(0,0,0,.28);
    padding: 28px;
    color: #eef8ff;
  }

  .auth-card h2 {
    font-size: 2rem;
    margin: 0 0 8px 0;
    font-weight: 900;
    letter-spacing: -0.03em;
  }

  .auth-card p {
    color: #7b90a6;
    margin: 0 0 18px 0;
  }

  .auth-label {
    display: block;
    margin: 12px 0 8px;
    font-weight: 700;
  }

  .auth-input {
    width: 100%;
    padding: 14px 16px;
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,.08);
    background: rgba(255,255,255,.03);
    color: #eef8ff;
    outline: none;
    box-sizing: border-box;
  }

  .auth-input:focus {
    border-color: rgba(0,232,255,.35);
    box-shadow: 0 0 0 3px rgba(0,232,255,.08);
  }

  .auth-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-top: 18px;
  }

  .auth-btn {
    padding: 14px 16px;
    border: none;
    border-radius: 14px;
    cursor: pointer;
    font-weight: 800;
    transition: .2s ease;
  }

  .auth-btn:hover {
    transform: translateY(-1px);
  }

  .auth-btn.primary {
    color: #04111d;
    background: linear-gradient(135deg, rgba(0,232,255,.95), rgba(18,217,159,.95));
  }

  .auth-btn.secondary {
    color: #eef8ff;
    background: rgba(255,255,255,.05);
    border: 1px solid rgba(255,255,255,.08);
  }

  .auth-msg {
    margin-top: 16px;
    min-height: 24px;
    font-weight: 700;
    line-height: 1.4;
  }

  .auth-msg.error {
    color: #ff4d7a;
  }

  .auth-msg.success {
    color: #12d99f;
  }

  .auth-userbar {
    position: fixed;
    top: 18px;
    right: 24px;
    z-index: 999998;
    display: flex;
    gap: 10px;
    align-items: center;
    flex-wrap: wrap;
  }

  .auth-pill {
    padding: 12px 14px;
    border-radius: 14px;
    background: rgba(8, 20, 33, 0.92);
    border: 1px solid rgba(0, 232, 255, 0.12);
    box-shadow: 0 0 0 1px rgba(0,232,255,.05), 0 14px 28px rgba(0,0,0,.28);
    color: #eef8ff;
    font-weight: 700;
    font-family: Inter, Arial, sans-serif;
  }

  .auth-pill.btn {
    color: #04111d;
    background: linear-gradient(135deg, rgba(0,232,255,.95), rgba(18,217,159,.95));
    border: none;
    cursor: pointer;
  }

  .hidden {
    display: none !important;
  }

  @media (max-width: 640px) {
    .auth-actions {
      grid-template-columns: 1fr;
    }

    .auth-userbar {
      left: 12px;
      right: 12px;
      top: 12px;
      justify-content: flex-end;
    }
  }
`;
document.head.appendChild(style);

document.documentElement.classList.add("auth-loading");
document.body.classList.add("auth-loading", "auth-locked");

const overlay = document.createElement("div");
overlay.id = "auth-overlay";
overlay.innerHTML = `
  <div class="auth-card">
    <h2>Entrar</h2>
    <p>Acesso restrito à dashboard.</p>

    <label class="auth-label" for="auth-email">E-mail</label>
    <input class="auth-input" type="email" id="auth-email" placeholder="seuemail@empresa.com" autocomplete="username">

    <label class="auth-label" for="auth-password">Senha</label>
    <input class="auth-input" type="password" id="auth-password" placeholder="Digite sua senha" autocomplete="current-password">

    <div class="auth-actions">
      <button class="auth-btn primary" id="auth-login-btn">Entrar</button>
      <button class="auth-btn secondary" id="auth-signup-btn">Criar acesso</button>
    </div>

    <div class="auth-msg" id="auth-msg"></div>
  </div>
`;
document.body.appendChild(overlay);

const userBar = document.createElement("div");
userBar.className = "auth-userbar hidden";
userBar.id = "auth-userbar";
userBar.innerHTML = `
  <div class="auth-pill" id="auth-user-email">Logado</div>
  <button class="auth-pill btn" id="auth-logout-btn">Sair</button>
`;
document.body.appendChild(userBar);

const emailInput = document.getElementById("auth-email");
const passwordInput = document.getElementById("auth-password");
const loginBtn = document.getElementById("auth-login-btn");
const signupBtn = document.getElementById("auth-signup-btn");
const logoutBtn = document.getElementById("auth-logout-btn");
const msgEl = document.getElementById("auth-msg");
const userEmailEl = document.getElementById("auth-user-email");

function normalizeEmail(email) {
  return String(email || "").trim().toLowerCase();
}

function setMsg(text, type = "error") {
  msgEl.className = `auth-msg ${type}`;
  msgEl.textContent = text || "";
}

function lockDashboard() {
  overlay.classList.remove("hidden");
  userBar.classList.add("hidden");
  document.body.classList.add("auth-locked");
  document.documentElement.classList.add("auth-loading");
  document.body.classList.add("auth-loading");
}

function unlockDashboard(email = "") {
  overlay.classList.add("hidden");
  userBar.classList.remove("hidden");
  userEmailEl.textContent = email || "Acesso liberado";
  document.body.classList.remove("auth-locked");
  document.documentElement.classList.remove("auth-loading");
  document.body.classList.remove("auth-loading");
}

async function isAllowed(email) {
  const normalized = normalizeEmail(email);

  const { data, error } = await supabase
    .from("allowed_users")
    .select("email, active")
    .eq("email", normalized)
    .eq("active", true);

  if (error) {
    console.error("Erro ao verificar permissão:", error);
    return false;
  }

  return Array.isArray(data) && data.length > 0;
}

function validateSupabaseConfig() {
  if (
    !SUPABASE_URL ||
    SUPABASE_URL.includes("COLE_AQUI") ||
    !SUPABASE_ANON_KEY ||
    SUPABASE_ANON_KEY.includes("COLE_AQUI")
  ) {
    setMsg("Preencha a URL e a anon key do Supabase no arquivo auth.js.");
    return false;
  }
  return true;
}

loginBtn.addEventListener("click", async () => {
  setMsg("");

  if (!validateSupabaseConfig()) return;

  const email = normalizeEmail(emailInput.value);
  const password = passwordInput.value;

  if (!email || !password) {
    setMsg("Preencha e-mail e senha.");
    return;
  }

  const { error } = await supabase.auth.signInWithPassword({
    email,
    password
  });

  if (error) {
    setMsg("Erro no login: " + error.message);
    return;
  }

  const allowed = await isAllowed(email);

  if (!allowed) {
    await supabase.auth.signOut();
    setMsg("Este e-mail não tem permissão para acessar a dashboard.");
    lockDashboard();
    return;
  }

  unlockDashboard(email);
});

signupBtn.addEventListener("click", async () => {
  setMsg("");

  if (!validateSupabaseConfig()) return;

  const email = normalizeEmail(emailInput.value);
  const password = passwordInput.value;

  if (!email || !password) {
    setMsg("Preencha e-mail e senha.");
    return;
  }

  try {
    const { data, error } = await supabase.auth.signUp({
      email,
      password
    });

    console.log("SIGNUP DATA:", data);
    console.log("SIGNUP ERROR:", error);

    if (error) {
      setMsg("Erro ao criar acesso: " + error.message);
      return;
    }

    setMsg("Acesso criado com sucesso. Agora clique em Entrar.", "success");
  } catch (err) {
    console.error("SIGNUP EXCEPTION:", err);
    setMsg("Erro ao criar acesso: " + (err?.message || "falha de conexão"));
  }
});

logoutBtn.addEventListener("click", async () => {
  await supabase.auth.signOut();
  lockDashboard();
  setMsg("");
});

async function validateSession() {
  if (!validateSupabaseConfig()) {
    lockDashboard();
    return;
  }

  const {
    data: { session }
  } = await supabase.auth.getSession();

  if (!session?.user?.email) {
    lockDashboard();
    return;
  }

  const allowed = await isAllowed(session.user.email);

  if (!allowed) {
    await supabase.auth.signOut();
    lockDashboard();
    setMsg("Seu e-mail não tem permissão para acessar esta dashboard.");
    return;
  }

  unlockDashboard(session.user.email);
}

supabase.auth.onAuthStateChange(async (_event, session) => {
  if (session?.user?.email) {
    const allowed = await isAllowed(session.user.email);

    if (allowed) {
      unlockDashboard(session.user.email);
    } else {
      await supabase.auth.signOut();
      lockDashboard();
      setMsg("Seu e-mail não tem permissão para acessar esta dashboard.");
    }
  } else {
    lockDashboard();
  }
});

await validateSession();
