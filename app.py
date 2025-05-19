import flet as ft
from pymongo import MongoClient

def main(page: ft.Page):
    # --- Conexão com MongoDB ---
    def conectar_mongodb():
        uri = "mongodb+srv://admin:123@avaliacao.lfoco.mongodb.net/?retryWrites=true&w=majority&appName=avaliacao"
        try:
            client = MongoClient(uri, server_api=ServerApi('1'))
            client.admin.command('ping')
            print('sucesso')
            return client
        except Exception as e:
            print(f"❌ Erro ao conectar ao MongoDB: {e}")
            return None
        
    # --- Inicialização da Aplicação ---
    client_mongo = conectar_mongodb()
    if not client_mongo:
        print('erro')

    db = client_mongo["avaliacoes"] 
    collection_geral = db["geral"]      

    # Consultar dados do MongoDB
    documentos = collection.find()

    # Criar uma lista para exibir os dados
    lista_dados = ft.ListView(expand=True)

    # Adicionar documentos à lista
    for documento in documentos:
        item = ft.Text(str(documento))
        lista_dados.controls.append(item)

    # Adicionar a lista ao conteúdo da página
    page.add(lista_dados)

# Executar o app Flet
ft.app(target=main)
