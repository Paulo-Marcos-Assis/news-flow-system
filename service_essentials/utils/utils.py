import requests
import json
import unicodedata
import time
import html
import re
import os
from bs4 import BeautifulSoup
#from langchain_core.messages import HumanMessage
#from langchain_ollama import ChatOllama

class Utils:
    @staticmethod
    def ask_model(self, prompt, field, model=os.getenv("MODEL_ASK_MODEL", "qwen2.5:0.5b")):
            GENERATE_URL = os.getenv("GENERATE_URL", "https://ollama-dev.ceos.ufsc.br/api/generate")
            #this should come from an environment variable or a singleton class
            #GENERATE_URL = "http://dgx.vlab.ufsc.br:11434/api/generate"
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stop": '<|endoftext|>',
                "options":{
                    "seed": 0,
                    "temperature": 0,
                    "num_ctx": 4096
                },
                "stream": False,
                "format": {
                    "type": "object",
                    "properties": {
                        field: {
                            "type": "string"
                        }
                    },
                    "required": [
                        field
                    ]
                }
            }
            
            
            for i in range(10):
                self.logger.info(f"""\n### Sending the following prompt to {model}\n{prompt}\n###""")
                for j in range(10):
                    try:
                        # Send the request to the Ollama API
                        response = requests.post(GENERATE_URL, json=payload)
                        # Check if the request was successful            
                        if response.status_code == 200:
                            # Parse and print the response from the LLM

                            response_data = response.json()
                            output = response_data.get("response")
                            break;                
                        else:
                            self.logger.error(f"Error: \n{response.status_code}, {response.text}")
                            self.logger.error("##########################################")
                            self.logger.error(f"##################### Size of prompt in characters: {len(payload['prompt'])}")
                            self.logger.error("##########################################")
                            self.logger.error(f"########################## Trying again in 6 seconds... trial #{j+1}")                
                            self.logger.error("##########################################")
                            output = ''
                            time.sleep(6)
                    except Exception as e:
                        self.logger.error(f"Error: \n{str(e)}")
                        self.logger.error("##########################################")
                        self.logger.error(f"##################### Size of prompt in characters: {len(payload['prompt'])}")
                        self.logger.error("##########################################")
                        self.logger.error(f"########################## Trying again in 6 seconds... trial #{i+1}")                
                        self.logger.error("##########################################")
                        time.sleep(6)
                if j<5:
                    self.logger.info(f"### Received the following output from {model}\n{response}\n###")
                    break
                else:
                    raise RuntimeError("Ollama server did not answer properly to ask_model method")
            try:
                output = json.loads(output) # em determinado momento esta linha deu erro
            except json.JSONDecodeError as e:
                print(f"Erro ao decodificar JSON: {e}")
                output = {}
            return output
        
    @staticmethod
    def extrair_primeira_pagina(html_text):
        # Esse método precisa ser melhor trabalhado
        # Divide o HTML em páginas assumindo que as páginas estão separadas por tags específicas
        # Por exemplo, você pode dividir com base em uma quebra de página comum
        soup = BeautifulSoup(html_text, "html.parser")

        # text = soup.get_text()
        # matches = list(re.finditer(r'\bP[áa]g(?:\.|(?:ina)?\.?)?\s*\d+\b', text, flags=re.IGNORECASE))
        #
        # if len(matches) == 0 or "1" not in matches[0].group():
        #     p_tags = soup.find_all("p")
        #     non_empty_p_tags = [p for p in p_tags if p.get_text(strip=True)][:20]
        #
        #     if len(non_empty_p_tags) > 0:
        #         text = ' '.join(p.get_text(strip=True) for p in non_empty_p_tags)
        #         return Utils.truncate_string(text)
        # else:
        #     start = matches[0].start()
        #     end = matches[1].start() if len(matches) > 1 else len(text)
        #
        #     text = text[start:end]
        #


        p_tags = soup.find_all()
        non_empty_p_tags = [p for p in p_tags if p.get_text(strip=False)]

        text = ' '.join(p.get_text(strip=False) for p in non_empty_p_tags)

        text = text.replace("\n", " ")
        text = text.replace("\t", " ")

        clean_result = re.sub(r'<[^>]*>|\s+', ' ', text)
        return Utils.truncate_string(Utils.clean_html_text(clean_result))
    
    @staticmethod
    def clean_html_text(input_text):
        """
        Remove tags HTML de um texto, converte entidades HTML para caracteres UTF-8
        e limita as quebras de linha a no máximo duas consecutivas.
        
        Args:
            input_text (str): Texto contendo HTML.
            
        Returns:
            str: Texto limpo sem HTML, com caracteres UTF-8 e no máximo duas quebras de linha consecutivas.
        """
        # Usar BeautifulSoup para remover tags HTML
        soup = BeautifulSoup(input_text, "html.parser")
        text_without_html = soup.get_text()

        # Decodificar entidades HTML para UTF-8
        text_utf8 = html.unescape(text_without_html)

        # Limitar quebras de linha consecutivas a no máximo duas
        text_limited_breaks = re.sub(r'\n{3,}', '\n\n', text_utf8)

        return text_limited_breaks.strip()
    
    def normalize_text(text):
        return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8').lower()

    def truncate_string(input_string, word_limit=2000):
        # Split the string into words
        words = input_string.split()
        
        # Check if the word count exceeds the limit
        if len(words) > word_limit:
            # Truncate the string to the first word_limit words and rejoin
            truncated_string = ' '.join(words[:word_limit])
            return truncated_string
        else:
            # If the string is already within the limit, return it as is
            return input_string
