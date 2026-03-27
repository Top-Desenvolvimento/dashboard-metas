import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm";

const RESET_VERSION = "RESET_20260327_01";
const SUPABASE_URL = "https://iahdagpmejyjspkktriw.supabase.co";
const SUPABASE_ANON_KEY = "COLE_AQUI_SUA_CHAVE_ANON_OU_PUBLISHABLE";

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

async function ensureRecoverySession() {
  const hash = window.location.hash || "";
  const query = window.location.search || "";

  if (!hash && !query) {
    setMsg("Link de recuperação inválido ou incompleto.");
    saveBtn.disabled = true;
    return false;
  }

  const {
    data: { session },
    error
  } = await supabase.auth.getSession();

  if (error) {
    setMsg("Erro ao validar sessão de recuperação: " + error.message);
    saveBtn.disabled = true;
    return false;
  }

  if (!session) {
    setMsg("Sessão de recuperação não encontrada. Abra novamente o link enviado por e-mail.");
    saveBtn.disabled = true;
    return false;
  }

  return true;
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
