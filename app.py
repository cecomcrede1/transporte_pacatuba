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
        google_creds_dict = {
            "type": st.secrets["google_credentials"]["type"],
            "project_id": st.secrets["google_credentials"]["project_id"],
            "private_key_id": st.secrets["google_credentials"]["private_key_id"],
            # CORREÇÃO IMPORTANTE para Invalid JWT Signature:
            "private_key": st.secrets["google_credentials"]["private_key"].replace('\\n', '\n'),
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
        sheet = client.open("transporte_escolar").sheet1 # Certifique-se que o nome da planilha está correto

        # Verificar se a planilha tem cabeçalhos, se não, adicioná-los
        # CORREÇÃO DO CABEÇALHO APLICADA:
        if not sheet.row_values(1): # Se a primeira linha estiver vazia
            sheet.append_row(["Escola", "INEP", "Nome Aluno", "Localidade", "Turma", "Data Cadastro"], value_input_option='USER_ENTERED')
        return sheet
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("Erro: Planilha 'transporte_escolar' não encontrada. Verifique o nome e as permissões de compartilhamento com o client_email da conta de serviço.")
        return None
    except KeyError as e:
        st.error(f"Erro ao acessar uma chave nos segredos do Streamlit: '{e}'. Verifique o arquivo .streamlit/secrets.toml (localmente) ou as configurações de Secrets no Streamlit Cloud.")
        st.error("Certifique-se de que todas as chaves necessárias (type, project_id, private_key, etc.) estão definidas sob [google_credentials].")
        return None
    except Exception as e:
        st.error(f"Erro ao conectar com o Google Sheets usando st.secrets: {e}")
        st.error("Verifique as configurações de Secrets, as permissões da API do Google Sheets no seu projeto Google Cloud e as permissões de compartilhamento da planilha.")
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
        if "confirmacao_escola_falhou" in st.session_state: # Limpar flag de erro se sucesso
            del st.session_state.confirmacao_escola_falhou
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

# --- Layout da Interface ---
col_logo1, col_titulo, col_logo2 = st.columns([1.5, 7, 1.5], vertical_alignment="bottom")

with col_logo1:
    # Substitua 'logo_CECOM_cinza2.png' pelo caminho correto ou URL se necessário, ou remova se não tiver a imagem.
    # st.image('logo_CECOM_cinza2.png', width=150)
    st.write("") # Placeholder se a imagem não estiver disponível
with col_titulo:
    st.title("Cadastro de Alunos para Transporte Escolar - Pacatuba")
with col_logo2:
    # Substitua 'cinza2.png' pelo caminho correto ou URL se necessário, ou remova se não tiver a imagem.
    # st.image('cinza2.png', width=150)
    st.write("") # Placeholder se a imagem não estiver disponível


# Etapa 1: Identificação da escola
if not st.session_state.escola or not st.session_state.inep:
    st.subheader("Informações da Escola")
    st.text_input("Nome da Escola", key="escola_input_field")
    st.text_input("Código INEP da Escola", key="inep_input_field")

    st.button("Confirmar Escola", on_click=callback_confirmar_escola)

    if "confirmacao_escola_falhou" in st.session_state and st.session_state.confirmacao_escola_falhou:
        # A verificação se os campos ainda estão vazios é feita implicitamente pela lógica do callback
        st.warning("Preencha todos os campos da escola corretamente.")
        # Não deletar a flag aqui permite que ela persista até uma ação que a limpe (como sucesso ou reiniciar)

# Etapa 2: Cadastro de Aluno (só aparece se a escola estiver confirmada e a conexão com a planilha OK)
elif sheet: # Adicionado para garantir que a planilha foi conectada
    st.success(f"Escola: {st.session_state.escola} | INEP: {st.session_state.inep}")
    st.divider()
    st.subheader("Cadastrar Aluno que necessita de transporte")

    with st.form("form_aluno", clear_on_submit=True):
        nome_aluno_form = st.text_input("Nome do Aluno", key="form_nome_aluno")
        localidade_form = st.text_input("Localidade", key="form_localidade")
        turma_form = st.text_input("Turma", key="form_turma")
        enviar_aluno_form = st.form_submit_button("➕ Adicionar Aluno à Lista")

        if enviar_aluno_form:
            if nome_aluno_form.strip() and localidade_form.strip() and turma_form.strip(): # Tornando turma obrigatória
                novo_aluno = {
                    "nome": nome_aluno_form.strip(),
                    "localidade": localidade_form.strip(),
                    'turma':turma_form.strip()
                }
                st.session_state.alunos_temp.append(novo_aluno)
                st.success(f"Aluno {nome_aluno_form.strip()} adicionado à lista temporária!")
            else:
                st.warning("Preencha todos os campos do aluno (Nome, Localidade e Turma).")

    # Exibir lista de alunos temporários e opções de gerenciamento
    if st.session_state.alunos_temp:
        st.divider()
        st.subheader("Lista de alunos a serem enviados")
        # Criar uma cópia para exibição para não modificar os dados originais com o índice
        df_display_data = [{"Nº": idx + 1, "Nome": aluno['nome'], "Localidade": aluno['localidade'], "Turma": aluno['turma']}
                           for idx, aluno in enumerate(st.session_state.alunos_temp)]
        df_display = pd.DataFrame(df_display_data)

        if not df_display.empty:
            st.dataframe(df_display.set_index("Nº"), use_container_width=True)

        col_acoes1, col_acoes2 = st.columns([2,3]) # Ajustado para melhor layout
        with col_acoes1:
            opcoes_excluir = [f"{idx + 1}. {aluno['nome']}" for idx, aluno in enumerate(st.session_state.alunos_temp)]
            if opcoes_excluir:
                aluno_selecionado_para_excluir_label = st.selectbox(
                    "Selecione o aluno para excluir da lista temporária:",
                    options=opcoes_excluir,
                    index=None, # Nenhum selecionado por padrão
                    placeholder="Escolha um aluno..."
                )
                if st.button("🗑️ Excluir Aluno Selecionado"):
                    if aluno_selecionado_para_excluir_label:
                        try:
                            indice_para_excluir = int(aluno_selecionado_para_excluir_label.split('.')[0]) - 1
                            if 0 <= indice_para_excluir < len(st.session_state.alunos_temp):
                                aluno_excluido = st.session_state.alunos_temp.pop(indice_para_excluir)
                                st.warning(f"Aluno {aluno_excluido['nome']} removido da lista!")
                                st.rerun() # Atualiza a interface
                            else:
                                st.error("Seleção inválida para exclusão.")
                        except (ValueError, IndexError):
                            st.error("Erro ao processar seleção para exclusão.")
                    else:
                        st.info("Nenhum aluno selecionado para exclusão.")
        with col_acoes2:
            st.write("") # Espaçamento
            st.write("") # Espaçamento
            if st.button("📤 Enviar Todos os Alunos para a Planilha", type="primary", disabled=not st.session_state.alunos_temp):
                try:
                    data_cadastro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    linhas_para_adicionar = []
                    for aluno_idx, aluno_data in enumerate(st.session_state.alunos_temp):
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
                        st.session_state.alunos_temp = [] # Limpar lista após envio
                        st.success(f"{total_enviados} aluno(s) enviado(s) com sucesso para a planilha!")
                        st.rerun() # Atualiza a interface
                    # Não precisa de 'else' aqui, pois o botão já está desabilitado se a lista estiver vazia
                except Exception as e:
                    st.error(f"Erro ao enviar dados para a planilha: {e}")
                    st.error("Verifique as permissões de escrita na planilha para a conta de serviço.")
elif not st.session_state.escola or not st.session_state.inep:
    pass # A seção de informação da escola já está sendo mostrada
else:
    # Isso acontece se a escola foi confirmada mas a conexão com a planilha falhou
    st.error("Não foi possível carregar a seção de cadastro de alunos pois a conexão com a planilha falhou. Verifique as mensagens de erro acima.")


# Botão para reiniciar o aplicativo (colocado no final para melhor fluxo)
st.divider()
if st.button("🔄 Reiniciar Tudo (Limpar Escola e Lista de Alunos)", on_click=callback_reiniciar_tudo):
    # A lógica está no callback. O st.rerun() é implícito após o on_click.
    # Uma mensagem explícita pode ser útil após o rerun, mas o próprio rerun limpa a tela.
    st.info("Aplicativo reiniciado.") # Esta mensagem aparecerá brevemente antes do rerun limpar
    st.rerun() # Força o rerun imediato para limpar a interface
