import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm";

const RESET_VERSION = "RESET_20260327_02";
const SUPABASE_URL = "https://iahdagpmejyispkktriw.supabase.co";
  const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlhaGRhZ3BtZWp5aXNwa2t0cml3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ1MTExMzYsImV4cCI6MjA5MDA4NzEzNn0.gEe_4VhSEHTiK1eA_Q8UmfTYEZqH7IueT03qGLsWCCk";

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true
  }
});

const newPasswordInput = document.getElementById("new-password");
const confirmPasswordInput = document.getElementById("confirm-password");
const saveBtn = document.getElementById("save-password-btn");
const msgEl = document.getElementById("msg");
const noteEl = document.getElementById("note");

noteEl.textContent = `${RESET_VERSION} | ${SUPABASE_URL}`;

function setMsg(text, type = "error") {
  msgEl.className = `msg ${type}`;
  msgEl.textContent = text || "";
}

function hasRecoveryParams() {
  const hash = window.location.hash || "";
  const search = window.location.search || "";

  return (
    hash.includes("access_token") ||
    hash.includes("refresh_token") ||
    hash.includes("type=recovery") ||
    search.includes("code=") ||
    search.includes("type=recovery")
  );
}

async function ensureRecoverySession() {
  if (!hasRecoveryParams()) {
    setMsg("Sessão de recuperação não encontrada. Abra novamente o link enviado por e-mail.");
    saveBtn.disabled = true;
    return false;
  }

  try {
    const { data, error } = await supabase.auth.getSession();

    if (error) {
      setMsg("Erro ao validar sessão de recuperação: " + error.message);
      saveBtn.disabled = true;
      return false;
    }

    if (!data.session) {
      setMsg("Sessão de recuperação não encontrada. Abra novamente o link enviado por e-mail.");
      saveBtn.disabled = true;
      return false;
    }

    return true;
  } catch (err) {
    console.error("RECOVERY SESSION ERROR:", err);
    setMsg("Erro ao validar recuperação.");
    saveBtn.disabled = true;
    return false;
  }
}

saveBtn.addEventListener("click", async () => {
  setMsg("");

  const newPassword = newPasswordInput.value;
  const confirmPassword = confirmPasswordInput.value;

  if (!newPassword || !confirmPassword) {
    setMsg("Preencha os dois campos.");
    return;
  }

  if (newPassword.length < 6) {
    setMsg("A nova senha deve ter pelo menos 6 caracteres.");
    return;
  }

  if (newPassword !== confirmPassword) {
    setMsg("As senhas não coincidem.");
    return;
  }

  saveBtn.disabled = true;

  try {
    const { error } = await supabase.auth.updateUser({
      password: newPassword
    });

    if (error) {
      setMsg("Erro ao salvar nova senha: " + error.message);
      return;
    }

    setMsg("Senha atualizada com sucesso. Você já pode voltar e entrar.", "success");
  } catch (err) {
    console.error("UPDATE PASSWORD EXCEPTION:", err);
    setMsg("Erro ao salvar nova senha: " + (err?.message || "falha de conexão"));
  } finally {
    saveBtn.disabled = false;
  }
});

await ensureRecoverySession();
