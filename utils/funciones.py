import json
import os
import time

import openai
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join('..', '.env'))

openai.api_key = os.getenv("OPENAI_API_KEY")
auth_token = os.getenv("AUTH_TOKEN")


headers = {"Content-Type": "application/json", "Authorization": f"Bearer {auth_token}"}
url = "https://api.awanllm.com/v1/chat/completions"  # URL for the API

def preguntar_gpt(prompt,
    sys_prompt= "Eres un asistente virtual que ayuda a los usuarios a obtener respuestas a sus preguntas.",
    model="gpt-3.5-turbo",
    max_retries=3,
    initial_delay=10,
    timeout=60,
    rate_limit_delay=5,
):
    """
    Envía un prompt a un modelo GPT y recupera la respuesta.
    Args:
        sys_prompt (str): El prompt del sistema para enviar al modelo GPT.
        prompt (str): El prompt del usuario para enviar al modelo GPT.
        model (str, opcional): El modelo GPT a utilizar. Por defecto es "gpt-3.5-turbo".
        max_retries (int, opcional): El número máximo de reintentos en caso de errores. Por defecto es 3.
        initial_delay (int, opcional): El retraso inicial entre reintentos en segundos. Por defecto es 10.
        timeout (int, opcional): El tiempo de espera para la solicitud HTTP en segundos. Por defecto es 60.
        rate_limit_delay (int, opcional): El retraso entre reintentos en caso de errores de límite de tasa. Por defecto es 5.
    Returns:
        str: La respuesta generada por el modelo GPT.
    Raises:
        openai.error.OpenAIError: Si ocurre un error específico de OpenAI durante la solicitud.
        requests.exceptions.Timeout: Si la solicitud agota el tiempo de espera.
        Exception: Si ocurre un error inesperado.
    """
    for attempt in range(max_retries):
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": prompt},
                ],
                timeout=timeout,
            )
            return response.choices[0].message.content
        except openai.error.RateLimitError as e:
            print(
                f"Intento {attempt + 1} fallido. Error: {e}. Límite de tasa excedido."
            )
            delay = rate_limit_delay
            print(f"Reintentando en {delay} segundos...")
            time.sleep(delay)
        except openai.error.APIError as e:
            print(f"Intento {attempt + 1} fallido. Error de API: {e}")
            delay = initial_delay
            print(f"Reintentando en {delay} segundos...")
            time.sleep(delay)
        except requests.exceptions.Timeout as e:
            print(f"Intento {attempt + 1} fallido por tiempo de espera excedido: {e}")
            if attempt < max_retries - 1:
                print("Reintentando...")
            time.sleep(initial_delay * (2**attempt))
        except Exception as e:
            print(f"Error no esperado: {e}")
            if attempt == max_retries - 1:
                return None  # Retornar None solo después de todos los intentos
    print("No se pudo completar la solicitud después de varios intentos.")
    return None



def preguntar_llama(
    sys_prompt, prompt, max_retries=3, initial_delay=10, timeout=60, rate_limit_delay=5
):
    """
    Sends a prompt to an AI model and retrieves the response.

    Args:
        sys_prompt (str): The system prompt to be sent to the AI model.
        prompt (str): The user prompt to be sent to the AI model.
        max_retries (int, optional): The maximum number of retries in case of errors. Defaults to 3.
        initial_delay (int, optional): The initial delay between retries in seconds. Defaults to 1.
        timeout (int, optional): The timeout for the HTTP request in seconds. Defaults to 60.
        rate_limit_delay (int, optional): The delay between retries in case of rate limiting errors. Defaults to 5.

    Returns:
        str: The response generated by the AI model.

    Raises:
        requests.exceptions.HTTPError: If an HTTP error occurs during the request.
        requests.exceptions.Timeout: If the request times out.
        Exception: If an unexpected error occurs.

    """
    payload = json.dumps(
        {
            "model": "Meta-Llama-3-8B-Instruct",
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt},
            ],
        }
    )

    for attempt in range(max_retries):
        try:
            response = requests.post(
                url, headers=headers, data=payload, timeout=timeout
            )
            response.raise_for_status()
            json_response = response.json()
            return json_response["choices"][0]["message"]["content"]
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            if status_code == 429:
                print(
                    f"Intento {attempt + 1} fallido. Error: {e}. Demasiadas solicitudes."
                )
                delay = rate_limit_delay
            elif status_code == 502:
                print(f"Intento {attempt + 1} fallido. Error: {e}. Error de Gateway.")
                delay = initial_delay
            else:
                print(f"Intento {attempt + 1} fallido. Error: {e}")
                break  # Salir del bucle si hay un error HTTP que no sea 429 o 502

            print(f"Reintentando en {delay} segundos...")
            time.sleep(delay)
        except requests.exceptions.Timeout as e:
            print(f"Intento {attempt + 1} fallido por tiempo de espera excedido: {e}")
            if attempt < max_retries - 1:
                print("Reintentando...")
            time.sleep(initial_delay * (2**attempt))
        except Exception as e:
            print(f"Error no esperado: {e}")
            if attempt == max_retries - 1:
                return None  # Retornar None solo después de todos los intentos

    print("No se pudo completar la solicitud después de varios intentos.")
    return None