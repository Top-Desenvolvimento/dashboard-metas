def ir_para_metas_por_url(driver, base_url, cidade) -> bool:
    """
    Plano B: abre direto a página REAL de metas (index2.php) e confirma que está em METAS.
    Também trata o redirecionamento index.php?redir=... (sessão não aplicada).
    """
    wait = WebDriverWait(driver, 30)

    try:
        metas_url = base_url.rstrip("/") + "/index2.php?conteudo=lista_metas"
        driver.get(metas_url)

        # Se o sistema jogar pra index.php?redir=..., tenta abrir metas de novo
        if "index.php?redir=" in driver.current_url:
            print(f"[DEBUG] {cidade} | redirecionou para index.php?redir, tentando novamente metas_url...")
            time.sleep(2)
            driver.get(metas_url)

        # Confirma que estamos na página de metas (não depende do id mes_ano)
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(translate(., 'METAS', 'metas'), 'metas')]")
            )
        )

        time.sleep(2)
        debug_state(driver, f"{cidade} | abriu metas via URL direta (ok)")
        return True

    except Exception as e:
        print(f"Erro ao abrir metas por URL em {cidade}: {e}")
        save_debug(driver, cidade, "falha_url_metas")
        return False
