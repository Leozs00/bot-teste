
import PyPDF2
from openai import OpenAI
from flask import Flask, request
from dotenv import load_dotenv
import os

# Carrega as variáveis de ambiente, como a chave da API do OpenAI, do arquivo .env
load_dotenv()

app = Flask(__name__)

# Inicializa o cliente OpenAI utilizando a chave de API carregada
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
modelo = "gpt-4"

#Define as personalidades do chatbot
personas = {
        'positivo': """
                    Assuma que você é um grande entusiasta de aprendizado de linguagem e fã de harry potter, você adora falar sobre os esses assuntos de forma feliz e positiva, adora usar palavras positivas e elogiar o usuário pelas perguntas sobre os assuntos.
        """,
        'neutro': """
                    Assuma que você é um chat pragmático e direto ao ponto, você responde com objetividade e clareza as perguntas, sem fugir do assunto e da pergunta feita, seja neutro e parcial em suas respostas.
        """,
        'negativo': """
                    Assuma que você é um solucionador compassivo, conhecido pela empatia, paciência e capacidade de entender as preocupações dos usuários. Você usa uma linguagem calorosa e acolhedora e não hesita em expressar apoio emocional através das palavras, caso o usuário utilize palavras negativas como: não gostei, não estou satisfeito ou coisas relacionadas, apenas tente confortá-lo e informar que vai melhorar para próxima pergunta.
        """
}

# Função para selecionar a persona com base na análise do sentimento da mensagem
def selecionar_persona(mensagem_usuario):
        prompt_sistema = """
            Faça uma análise da mensagem informada abaixo para identificar se o sentimento é: positivo, neutro ou negativo.
            Retorne apenas um dos três tipos de sentimentos informados como resposta.
        """
        response = client.chat.completions.create(
            model=modelo,
            messages=[
                {
                  "role": "system",
                  "content": prompt_sistema
                },

                {
                  "role": "user",
                  "content": mensagem_usuario
                }
            ],
            temperature=1
        )
        return response.choices[0].message.content.lower().strip()


# Função que lê o conteúdo de um arquivo PDF e retorna o texto extraído
def conteudo(lista_caminhos_pdf): 
    textos = ""  # Inicializa uma string vazia para armazenar o texto extraíando
    for caminho_pdf in lista_caminhos_pdf:
     with open(caminho_pdf, 'rb') as file:  # Abre o arquivo PDF em modo de leitura binária
        reader = PyPDF2.PdfReader(file)  # Cria um leitor de PDF
        # Itera por cada página do PDF e extrai o texto
        for page in reader.pages:
            textos += page.extract_text()  
    return textos  # Retorna o texto completo extraído do PDF

# Função principal para gerar a resposta do chat usando a API do OpenAI
def funcao(historico):
    # Faz uma chamada para o modelo de chat da OpenAI, enviando o histórico de mensagens
    completion = client.chat.completions.create(
        model="gpt-4o-mini",  # Modelo utilizado para geração de respostas
        messages=historico,  # O histórico de conversas é enviado ao modelo
        temperature=0,  # Define a temperatura (criatividade) das respostas
        max_tokens=200  # Limita a resposta a 200 tokens
    )
    
    # Retorna o conteúdo da primeira escolha de resposta gerada pelo modelo
    return completion.choices[0].message.content

# Função principal do chatbot
def chatbot():
    # Lê o conteúdo do PDF especificado e armazena na variável textos_pdf
    lista_caminhos_pdf = [
                "./arquivos/textoHP.pdf",
                "./arquivos/aprendizado.pdf"
                
     ]

    textos_pdf = conteudo(lista_caminhos_pdf)


    # Define o contexto do chatbot: ele só pode responder perguntas com base no conteúdo do PDF
    historico = [
        {
            "role": "system", 
            "content": f"Você é um chatbot que passa informações rápidas e objetivas, porém somente sobre o conteúdo retirado deste documento: {textos_pdf}. "
                       "Caso sejam feitas perguntas que fujam do assunto retirado do documento, apenas responda: "
                       "'Infelizmente não posso responder a sua dúvida, tiro dúvidas somente sobre Harry Potter'."
                       "Sempre seja objetivo nas suas respostas, tentando utilizar o menor número de caracteres sem afetar a construção da resposta."
                       "Lembre-se que perguntas do cotidiano devem ser respondidas, como por exemplo: oi, tudo bem, tchau e coisas relacionadas, sempre visando a boa educação e cordialidade com o usuário"
                       
        }
    ]

    opcoes_de_sair = ['sair', 'Sair', 'encerrar', 'parar']

    # Loop para manter o chat rodando até o usuário digitar 'sair'
    while True:
        # Solicita uma pergunta do usuário
        faca_pergunta = input("Olá, respondo perguntas sobre o assunto Harry Potter, caso queira encerrar digite 'sair': ")
        
        # Se o usuário digitar 'sair', o loop é encerrado
        if faca_pergunta.lower() in opcoes_de_sair:
            print("Espero ter ajudado, até a próxima :)")
            break

        # Selecionar a persona com base no sentimento da pergunta do usuário
        sentimento = selecionar_persona(faca_pergunta)
        persona_escolhida = personas.get(sentimento, personas['neutro']) # Usar 'neutro' como padrão se o sentimento não for detectado

        # Adicionar a persona ao contexto do sistema
        historico.append({"role": "system", "content": persona_escolhida})
        
        # Adiciona a pergunta do usuário ao histórico
        historico.append({"role": "user", "content": faca_pergunta})

        # Obtém a resposta do chatbot chamando a função 'funcao'
        resposta = funcao(historico)

        # Adiciona a resposta do chatbot ao histórico
        historico.append({"role": "system", "content": resposta})

        # Exibe a resposta do chatbot ao usuário
        print(resposta)

# Ponto de entrada do programa
if __name__ == "__main__":
    chatbot()