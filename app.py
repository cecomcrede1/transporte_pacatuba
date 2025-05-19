import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime # Importar datetime no início

st.set_page_config(page_title="Cadastro de Alunos para Transporte Escolar - Pacatuba", layout="wide")

# Conectar ao Google Sheets usando st.secrets
@st.cache_resource
def conectar_planilha():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

        # Carregar credenciais do st.secrets
        # Certifique-se de que a estrutura em st.secrets["google_credentials"]
        # corresponde ao conteúdo do seu arquivo JSON de credenciais.
        google_creds_dict = {
            "type": st.secrets["google_credentials"]["type"],
            "project_id": st.secrets["google_credentials"]["project_id"],
            "private_key_id": st.secrets["google_credentials"]["private_key_id"],
            "private_key": st.secrets["google_credentials"]["private_key"], # O Streamlit lida bem com strings multilinhas do TOML
            "client_email": st.secrets["google_credentials"]["client_email"],
            "client_id": st.secrets["google_credentials"]["client_id"],
            "auth_uri": st.secrets["google_credentials"]["auth_uri"],
            "token_uri": st.secrets["google_credentials"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["google_credentials"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["google_credentials"]["client_x509_cert_url"]
        }
        # Adicionar "universe_domain" se estiver presente nas suas credenciais e for necessário
        if "universe_domain" in st.secrets["google_credentials"]:
             google_creds_dict["universe_domain"] = st.secrets["google_credentials"]["universe_domain"]


        creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open("transporte_escolar").sheet1

        # Verificar se a planilha tem cabeçalhos, se não, adicioná-los
        # CORREÇÃO DO CABEÇALHO APLICADA:
        if not sheet.row_values(1): # Se a primeira linha estiver vazia
            sheet.append_row(["Escola", "INEP", "Nome Aluno", "Localidade", "Turma", "Data Cadastro"], value_input_option='USER_ENTERED')
        return sheet
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("Erro: Planilha 'transporte_escolar' não encontrada. Verifique o nome e as permissões.")
        return None
    except KeyError as e:
        st.error(f"Erro ao acessar uma chave nos segredos do Streamlit: {e}. Verifique o arquivo .streamlit/secrets.toml e a seção [google_credentials].")
        st.error("Certifique-se de que todas as chaves necessárias (type, project_id, private_key, etc.) estão definidas.")
        return None
    except Exception as e:
        st.error(f"Erro ao conectar com o Google Sheets usando st.secrets: {e}")
        st.error("Verifique as configurações em .streamlit/secrets.toml, as permissões da API do Google Sheets e as permissões da planilha.")
        return None

sheet = conectar_planilha()

# --- Estado da Sessão e Funções de Callback ---
if "escola" not in st.session_state:
    st.session_state.escola = ""
if "inep" not in st.session_state:
    st.session_state.inep = ""
if "alunos_temp" not in st.session_state:
    st.session_state.alunos_temp = []

# Para os campos de input da escola (gerenciados por chaves)
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
    else:
        st.session_state.confirmacao_escola_falhou = True

def callback_reiniciar_tudo():
    # CORREÇÃO APLICADA: "form_turma" adicionado
    keys_to_clear = ["escola", "inep", "alunos_temp",
                     "escola_input_field", "inep_input_field",
                     "form_nome_aluno", "form_localidade", "form_turma"]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    if "confirmacao_escola_falhou" in st.session_state:
        del st.session_state.confirmacao_escola_falhou

col1, col2, col3 = st.columns([1.5,7,1.5], vertical_alignment="bottom")

with col1:
    st.image('logo_CECOM_cinza2.png', width=150) # Certifique-se que este arquivo de imagem existe
with col2:
    st.title("Cadastro de Alunos para Transporte Escolar - Pacatuba")
with col3:
    st.image('cinza2.png', width=150) # Certifique-se que este arquivo de imagem existe

# Etapa 1: Identificação da escola
if not st.session_state.escola or not st.session_state.inep:
    st.subheader("Informações da Escola")
    escola_input = st.text_input("Nome da Escola", key="escola_input_field")
    inep_input = st.text_input("Código INEP da Escola", key="inep_input_field")

    if st.button("Confirmar Escola", on_click=callback_confirmar_escola):
        pass

    if "confirmacao_escola_falhou" in st.session_state and st.session_state.confirmacao_escola_falhou:
        if not st.session_state.escola_input_field.strip() or not st.session_state.inep_input_field.strip():
             st.warning("Preencha todos os campos da escola corretamente.")
        del st.session_state.confirmacao_escola_falhou

else:
    st.success(f"Escola: {st.session_state.escola} | INEP: {st.session_state.inep}")

    st.subheader("Cadastrar Aluno que necessita de transporte")
    with st.form("form_aluno", clear_on_submit=True):
        nome_aluno_form = st.text_input("Nome do Aluno", key="form_nome_aluno")
        localidade_form = st.text_input("Localidade", key="form_localidade")
        turma_form = st.text_input("Turma", key="form_turma") # CONSIDERAÇÃO: Tornar este campo obrigatório na validação se necessário
        enviar_aluno_form = st.form_submit_button("➕ Adicionar Aluno à Lista")

        if enviar_aluno_form:
            # CONSIDERAÇÃO: Adicionar turma_form.strip() à condição se for obrigatório
            if nome_aluno_form.strip() and localidade_form.strip() and turma_form.strip(): # Exemplo com turma obrigatória
                novo_aluno = {
                    "nome": nome_aluno_form.strip(),
                    "localidade": localidade_form.strip(),
                    'turma':turma_form.strip()
                }
                st.session_state.alunos_temp.append(novo_aluno)
                st.success(f"Aluno {nome_aluno_form.strip()} adicionado à lista temporária!")
            else:
                # Ajustar mensagem de aviso se a turma for opcional ou obrigatória
                st.warning("Preencha todos os campos do aluno (Nome, Localidade e Turma).")


    if st.session_state.alunos_temp:
        st.subheader("Lista de alunos a serem enviados")
        df_display = pd.DataFrame(list(st.session_state.alunos_temp))
        if not df_display.empty:
            df_display.index = range(1, len(df_display) + 1)
            st.dataframe(df_display[['nome', 'localidade', 'turma']])

        col_acoes1, col_acoes2 = st.columns([2,3])
        with col_acoes1:
            if st.session_state.alunos_temp:
                opcoes_excluir = [f"{idx + 1}. {aluno['nome']}" for idx, aluno in enumerate(st.session_state.alunos_temp)]
                if opcoes_excluir:
                    aluno_selecionado_para_excluir = st.selectbox(
                        "Selecione o aluno para excluir:",
                        options=opcoes_excluir,
                        index=None,
                        placeholder="Escolha um aluno..."
                    )
                    if st.button("🗑️ Excluir Aluno Selecionado"):
                        if aluno_selecionado_para_excluir:
                            indice_para_excluir = int(aluno_selecionado_para_excluir.split('.')[0]) - 1
                            if 0 <= indice_para_excluir < len(st.session_state.alunos_temp):
                                aluno_excluido = st.session_state.alunos_temp.pop(indice_para_excluir)
                                st.warning(f"Aluno {aluno_excluido['nome']} removido da lista!")
                                st.rerun()
                            else:
                                st.error("Seleção inválida para exclusão.")
                        else:
                            st.info("Nenhum aluno selecionado para exclusão.")
        with col_acoes2:
            st.write("") # Para espaçamento, se necessário
            st.write("") # Para espaçamento, se necessário
            if st.button("📤 Enviar Todos os Alunos para a Planilha", type="primary", disabled=not sheet or not st.session_state.alunos_temp):
                if sheet and st.session_state.alunos_temp:
                    try:
                        data_cadastro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        linhas_para_adicionar = []
                        for aluno in st.session_state.alunos_temp:
                            nova_linha = [
                                st.session_state.escola,
                                st.session_state.inep,
                                aluno["nome"],
                                aluno["localidade"],
                                aluno["turma"], # 'turma' já estava sendo coletada e agora será enviada corretamente devido à correção do cabeçalho
                                data_cadastro
                            ]
                            linhas_para_adicionar.append(nova_linha)

                        if linhas_para_adicionar:
                            sheet.append_rows(linhas_para_adicionar, value_input_option='USER_ENTERED')
                            total_enviados = len(st.session_state.alunos_temp)
                            st.session_state.alunos_temp = []
                            st.success(f"{total_enviados} aluno(s) enviado(s) com sucesso para a planilha!")
                            st.rerun()
                        else:
                            st.warning("Não há alunos na lista para enviar.")
                    except Exception as e:
                        st.error(f"Erro ao enviar dados para a planilha: {e}")
                elif not sheet:
                    st.error("Conexão com a planilha não estabelecida. Não é possível enviar os dados.")
                else:
                    st.warning("Não há alunos na lista para enviar.")

if st.button("🔄 Reiniciar Tudo", on_click=callback_reiniciar_tudo):
    pass
