import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

st.set_page_config(page_title="Cadastro de Alunos para Transporte Escolar - Pacatuba", layout="wide")

# Conectar ao Google Sheets
@st.cache_resource
def conectar_planilha():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("transporte_escolar").sheet1
        # Verificar se a planilha tem cabeçalhos, se não, adicioná-los
        if not sheet.row_values(1): # Se a primeira linha estiver vazia
            sheet.append_row(["Escola", "INEP", "Nome Aluno", "Localidade", "Data Cadastro"])
        return sheet
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("Erro: Planilha 'transporte_escolar' não encontrada. Verifique o nome e as permissões.")
        return None
    except FileNotFoundError:
        st.error("Erro: Arquivo 'credenciais.json' não encontrado. Verifique o caminho.")
        return None
    except Exception as e:
        st.error(f"Erro ao conectar com o Google Sheets: {e}")
        st.error("Verifique as configurações de 'credenciais.json' e as permissões da planilha.")
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
    # Esta função será chamada ANTES do rerun do script principal
    # quando o botão "Confirmar Escola" for clicado.
    # Os valores dos inputs já estarão no session_state devido às suas keys.
    escola_val = st.session_state.escola_input_field
    inep_val = st.session_state.inep_input_field

    if escola_val.strip() and inep_val.strip():
        st.session_state.escola = escola_val.strip()
        st.session_state.inep = inep_val.strip()
        # Limpar os valores no session_state para os inputs
        # Isso fará com que os campos de texto apareçam vazios no próximo rerun
        st.session_state.escola_input_field = ""
        st.session_state.inep_input_field = ""
    else:
        # Se não quisermos limpar e apenas mostrar o aviso,
        # o rerun do botão já fará com que o script principal mostre o aviso.
        # Guardamos a informação que a tentativa de confirmação falhou para mostrar o aviso.
        st.session_state.confirmacao_escola_falhou = True

def callback_reiniciar_tudo():
    keys_to_clear = ["escola", "inep", "alunos_temp",
                     "escola_input_field", "inep_input_field",
                     "form_nome_aluno", "form_localidade"] # Adicionar chaves dos campos do formulário
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    # Resetar flags de controle
    if "confirmacao_escola_falhou" in st.session_state:
        del st.session_state.confirmacao_escola_falhou

col1, col2, col3 = st.columns([1.5,7,1.5], vertical_alignment="bottom")

with col1:
    st.image('logo_CECOM_cinza2.png', width=150)
with col2:
    st.title("Cadastro de Alunos para Transporte Escolar - Pacatuba")
with col3:
    st.image('cinza2.png', width=150)

# Etapa 1: Identificação da escola
if not st.session_state.escola or not st.session_state.inep:
    st.subheader("Informações da Escola")
    escola_input = st.text_input("Nome da Escola", key="escola_input_field")
    inep_input = st.text_input("Código INEP da Escola", key="inep_input_field")

    if st.button("Confirmar Escola", on_click=callback_confirmar_escola):
        # A lógica principal agora está no callback.
        # O rerun acontece automaticamente após o callback e o clique do botão.
        # Podemos verificar a flag para mostrar o aviso aqui, após o rerun.
        pass # O callback faz o trabalho. st.rerun() é implícito.

    # Mostrar aviso se a tentativa de confirmação falhou (após o rerun do callback)
    if "confirmacao_escola_falhou" in st.session_state and st.session_state.confirmacao_escola_falhou:
        if not st.session_state.escola_input_field.strip() or not st.session_state.inep_input_field.strip():
             st.warning("Preencha todos os campos da escola corretamente.")
        del st.session_state.confirmacao_escola_falhou # Limpar a flag

else:
    st.success(f"Escola: {st.session_state.escola} | INEP: {st.session_state.inep}")

    # Etapa 2: Cadastro de Aluno
    st.subheader("Cadastrar Aluno que necessita de transporte")
    # Usar clear_on_submit=True é a forma correta para formulários.
    # As chaves dos widgets dentro do formulário são importantes.
    with st.form("form_aluno", clear_on_submit=True):
        nome_aluno_form = st.text_input("Nome do Aluno", key="form_nome_aluno")
        localidade_form = st.text_input("Localidade", key="form_localidade")
        turma_form = st.text_input("Turma", key="form_turma")
        enviar_aluno_form = st.form_submit_button("➕ Adicionar Aluno à Lista")

        if enviar_aluno_form:
            if nome_aluno_form.strip() and localidade_form.strip():
                novo_aluno = {
                    "nome": nome_aluno_form.strip(),
                    "localidade": localidade_form.strip(),
                    'turma':turma_form.strip()
                }
                st.session_state.alunos_temp.append(novo_aluno)
                st.success(f"Aluno {nome_aluno_form.strip()} adicionado à lista temporária!")
                # st.rerun() # Não é necessário aqui, o form e o clear_on_submit cuidam do rerun
            else:
                st.warning("Preencha todos os campos do aluno.")
                # Se houver um warning, o clear_on_submit não vai limpar os campos, o que é bom.

    # Exibir lista de alunos temporários
    if st.session_state.alunos_temp:
        st.subheader("Lista de alunos a serem enviados")
        df_display = pd.DataFrame(list(st.session_state.alunos_temp))
        if not df_display.empty:
            df_display.index = range(1, len(df_display) + 1)
            st.dataframe(df_display[['nome', 'localidade', 'turma']])

        col1, col2 = st.columns([2,3])
        with col1:
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
        with col2:
            st.write("")
            st.write("")
            if st.button("📤 Enviar Todos os Alunos para a Planilha", type="primary", disabled=not sheet or not st.session_state.alunos_temp):
                if sheet and st.session_state.alunos_temp:
                    try:
                        from datetime import datetime
                        data_cadastro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        linhas_para_adicionar = []
                        for aluno in st.session_state.alunos_temp:
                            nova_linha = [
                                st.session_state.escola,
                                st.session_state.inep,
                                aluno["nome"],
                                aluno["localidade"],
                                aluno["turma"],
                                data_cadastro # Adicionando data/hora do cadastro
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

# Botão para reiniciar o aplicativo
if st.button("🔄 Reiniciar Tudo", on_click=callback_reiniciar_tudo):
    # A lógica está no callback. O st.rerun() é implícito após o on_click.
    pass
