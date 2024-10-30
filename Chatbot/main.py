import os
import requests
import PyPDF2
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)

# Inicializa o cliente OpenAI utilizando a chave de API carregada
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
whatsapp_token = os.getenv("WHATSAPP_TOKEN")
whatsapp_phone_id = os.getenv("NUMBER_ID")
VERIFY_TOKEN = "my_verify_token"
modelo = "gpt-4o-mini"

# Define as personalidades do chatbot
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
    response = client.chat_completions.create(
        model=modelo,
        messages=[
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": mensagem_usuario}
        ],
        temperature=1
    )
    return response.choices[0].message.content.lower().strip()

# Função que lê o conteúdo de um arquivo PDF e retorna o texto extraído
def conteudo(lista_caminhos_pdf):
    textos = ""
    for caminho_pdf in lista_caminhos_pdf:
        with open(caminho_pdf, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                textos += page.extract_text()
    return textos

# Função principal para gerar a resposta do chat usando a API do OpenAI
def funcao(historico):
    completion = client.chat_completions.create(
        model=modelo,
        messages=historico,
        temperature=0,
        max_tokens=200
    )
    return completion.choices[0].message.content

# Endpoint webhook para receber e responder mensagens do WhatsApp
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        
        if mode and token:
            if mode == "subscribe" and token == VERIFY_TOKEN:
                return challenge, 200
            else:
                return "Forbidden", 403

    if request.method == "POST":
        data = request.get_json()
        app.logger.info(f"Received webhook data: {data}")
        if data["object"] == "whatsapp_business_account":
            for entry in data["entry"]:
                for change in entry["changes"]:
                    if "messages" in change["value"]:
                        for message in change["value"]["messages"]:
                            if message["type"] == "text":
                                phone_number = message["from"]
                                text = message["text"]["body"]
                                
                                # Selecionar a persona com base no sentimento da pergunta do usuário
                                sentimento = selecionar_persona(text)
                                persona_escolhida = personas.get(sentimento, personas['neutro'])

                                # Define o contexto do chatbot: ele só pode responder perguntas com base no conteúdo do PDF
                                lista_caminhos_pdf = ["./arquivos/textoHP.pdf", "./arquivos/aprendizado.pdf"]
                                textos_pdf = conteudo(lista_caminhos_pdf)
                                historico = [
                                    {"role": "system", "content": persona_escolhida},
                                    {"role": "user", "content": text}
                                ]

                                resposta = funcao(historico)
                                send_whatsapp_message(phone_number, resposta)
        return jsonify({"status": "success"}), 200

# Função para enviar mensagens via WhatsApp
def send_whatsapp_message(phone_number, message):
    url = f"https://graph.facebook.com/v13.0/{whatsapp_phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {whatsapp_token}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {
            "body": message
        }
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

# Ponto de entrada do programa
if __name__ == "__main__":
    app.run(port=5000, debug=True)
