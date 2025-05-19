import streamlit as st
import gspread
from google.oauth2.service_account import Credentials # MUDANÇA AQUI
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Cadastro de Alunos para Transporte Escolar - Pacatuba", layout="wide")

@st.cache_resource
def conectar_planilha():
    try:
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

        # Carregar credenciais do st.secrets
        google_creds_dict_info = {
            "type": st.secrets["google_credentials"]["type"],
            "project_id": st.secrets["google_credentials"]["project_id"],
            "private_key_id": st.secrets["google_credentials"]["private_key_id"],
            "private_key": st.secrets["google_credentials"]["private_key"].replace('\\n', '\n'), # Mantém a correção
            "client_email": st.secrets["google_credentials"]["client_email"],
            "client_id": st.secrets["google_credentials"]["client_id"],
            "auth_uri": st.secrets["google_credentials"]["auth_uri"],
            "token_uri": st.secrets["google_credentials"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["google_credentials"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["google_credentials"]["client_x509_cert_url"]
        }
        if "universe_domain" in st.secrets["google_credentials"]:
             google_creds_dict_info["universe_domain"] = st.secrets["google_credentials"]["universe_domain"]

        # MUDANÇA PARA USAR google-auth
        creds = Credentials.from_service_account_info(google_creds_dict_info, scopes=scopes)
        client = gspread.authorize(creds) # gspread lida bem com credenciais de google-auth

        sheet = client.open("transporte_escolar").sheet1

        if not sheet.row_values(1):
            sheet.append_row(["Escola", "INEP", "Nome Aluno", "Localidade", "Turma", "Data Cadastro"], value_input_option='USER_ENTERED')
        return sheet
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("Erro: Planilha 'transporte_escolar' não encontrada. Verifique o nome e as permissões de compartilhamento com o client_email da conta de serviço.")
        return None
    except KeyError as e:
        st.error(f"Erro ao acessar uma chave nos segredos do Streamlit: '{e}'. Verifique as configurações de Secrets no Streamlit Cloud.")
        st.error("Certifique-se de que todas as chaves necessárias (type, project_id, private_key, etc.) estão definidas sob [google_credentials].")
        return None
    except Exception as e: # Captura exceções mais específicas de autenticação se possível
        st.error(f"Erro ao conectar com o Google Sheets: {e}")
        st.error("Verifique as configurações de Secrets, as permissões da API do Google Sheets e Drive no seu projeto Google Cloud, e as permissões de compartilhamento da planilha.")
        return None

# O restante do seu código continua igual...
sheet = conectar_planilha()

# --- Estado da Sessão e Funções de Callback ---
if "escola" not in st.session_state:
    st.session_state.escola = ""
if "inep" not in st.session_state:
    st.session_state.inep = ""
if "alunos_temp" not in st.session_state:
    st.session_state.alunos_temp = []

if "escola_input_field" not in st.session_state:
    st.session_state.escola_input_field = ""
if "inep_input_field" not in st.session_state:
    st.session_state.inep_input_field = ""


def callback_confirmar_escola():
    escola_val = st.session_state.escola_input_field
    inep_val = st.session_state.inep_input_field

    if escola_val.strip() and inep_val.strip():
        st.session_state.escola = escola_val.strip()
        st.session_state.inep = inep_val.strip()
        st.session_state.escola_input_field = ""
        st.session_state.inep_input_field = ""
        if "confirmacao_escola_falhou" in st.session_state:
            del st.session_state.confirmacao_escola_falhou
    else:
        st.session_state.confirmacao_escola_falhou = True

def callback_reiniciar_tudo():
    keys_to_clear = ["escola", "inep", "alunos_temp",
                     "escola_input_field", "inep_input_field",
                     "form_nome_aluno", "form_localidade", "form_turma"]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    if "confirmacao_escola_falhou" in st.session_state:
        del st.session_state.confirmacao_escola_falhou

col_logo1, col_titulo, col_logo2 = st.columns([1.5, 7, 1.5], vertical_alignment="bottom")

with col_logo1:
    st.image('logo_CECOM_cinza2.png', width=150)
    st.write("")
with col_titulo:
    st.title("Cadastro de Alunos para Transporte Escolar - Pacatuba")
with col_logo2:
    st.image('cinza2.png', width=150)
    st.write("")


if not st.session_state.escola or not st.session_state.inep:
    st.subheader("Informações da Escola")
    st.text_input("Nome da Escola", key="escola_input_field")
    st.text_input("Código INEP da Escola", key="inep_input_field")
    st.button("Confirmar Escola", on_click=callback_confirmar_escola)
    if "confirmacao_escola_falhou" in st.session_state and st.session_state.confirmacao_escola_falhou:
        st.warning("Preencha todos os campos da escola corretamente.")

elif sheet:
    st.success(f"Escola: {st.session_state.escola} | INEP: {st.session_state.inep}")
    st.divider()
    st.subheader("Cadastrar Aluno que necessita de transporte")

    with st.form("form_aluno", clear_on_submit=True):
        nome_aluno_form = st.text_input("Nome do Aluno", key="form_nome_aluno")
        localidade_form = st.text_input("Localidade", key="form_localidade")
        turma_form = st.text_input("Turma", key="form_turma")
        enviar_aluno_form = st.form_submit_button("➕ Adicionar Aluno à Lista")

        if enviar_aluno_form:
            if nome_aluno_form.strip() and localidade_form.strip() and turma_form.strip():
                novo_aluno = {
                    "nome": nome_aluno_form.strip(),
                    "localidade": localidade_form.strip(),
                    'turma':turma_form.strip()
                }
                st.session_state.alunos_temp.append(novo_aluno)
                st.success(f"Aluno {nome_aluno_form.strip()} adicionado à lista temporária!")
            else:
                st.warning("Preencha todos os campos do aluno (Nome, Localidade e Turma).")

    if st.session_state.alunos_temp:
        st.divider()
        st.subheader("Lista de alunos a serem enviados")
        df_display_data = [{"Nº": idx + 1, "Nome": aluno['nome'], "Localidade": aluno['localidade'], "Turma": aluno['turma']}
                           for idx, aluno in enumerate(st.session_state.alunos_temp)]
        df_display = pd.DataFrame(df_display_data)
        if not df_display.empty:
            st.dataframe(df_display.set_index("Nº"), use_container_width=True)

        col_acoes1, col_acoes2 = st.columns([2,3])
        with col_acoes1:
            opcoes_excluir = [f"{idx + 1}. {aluno['nome']}" for idx, aluno in enumerate(st.session_state.alunos_temp)]
            if opcoes_excluir:
                aluno_selecionado_para_excluir_label = st.selectbox(
                    "Selecione o aluno para excluir da lista temporária:",
                    options=opcoes_excluir,
                    index=None,
                    placeholder="Escolha um aluno..."
                )
                if st.button("🗑️ Excluir Aluno Selecionado"):
                    if aluno_selecionado_para_excluir_label:
                        try:
                            indice_para_excluir = int(aluno_selecionado_para_excluir_label.split('.')[0]) - 1
                            if 0 <= indice_para_excluir < len(st.session_state.alunos_temp):
                                aluno_excluido = st.session_state.alunos_temp.pop(indice_para_excluir)
                                st.warning(f"Aluno {aluno_excluido['nome']} removido da lista!")
                                st.rerun()
                            else:
                                st.error("Seleção inválida para exclusão.")
                        except (ValueError, IndexError):
                            st.error("Erro ao processar seleção para exclusão.")
                    else:
                        st.info("Nenhum aluno selecionado para exclusão.")
        with col_acoes2:
            st.write("")
            st.write("")
            if st.button("📤 Enviar Todos os Alunos para a Planilha", type="primary", disabled=not st.session_state.alunos_temp):
                try:
                    data_cadastro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    linhas_para_adicionar = []
                    for aluno_data in st.session_state.alunos_temp:
                        nova_linha = [
                            st.session_state.escola,
                            st.session_state.inep,
                            aluno_data["nome"],
                            aluno_data["localidade"],
                            aluno_data["turma"],
                            data_cadastro
                        ]
                        linhas_para_adicionar.append(nova_linha)
                    if linhas_para_adicionar:
                        sheet.append_rows(linhas_para_adicionar, value_input_option='USER_ENTERED')
                        total_enviados = len(st.session_state.alunos_temp)
                        st.session_state.alunos_temp = []
                        st.success(f"{total_enviados} aluno(s) enviado(s) com sucesso para a planilha!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Erro ao enviar dados para a planilha: {e}")
                    st.error("Verifique as permissões de escrita na planilha para a conta de serviço.")
elif not st.session_state.escola or not st.session_state.inep:
    pass
else:
    st.error("Não foi possível carregar a seção de cadastro de alunos pois a conexão com a planilha falhou. Verifique as mensagens de erro acima.")

st.divider()
if st.button("🔄 Reiniciar Tudo (Limpar Escola e Lista de Alunos)", on_click=callback_reiniciar_tudo):
    st.info("Aplicativo reiniciado.")
    st.rerun()
