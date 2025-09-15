import json
import os
import requests
from random import choice
import string
import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np

#Token Chatbot Telegram
with open('/content/drive/MyDrive/Modelo/key.bin', 'r') as f:
    TOKEN = f.read()

URL = 'https://api.telegram.org/bot' + TOKEN + '/'
PHOTO_DIRECTORY = 'telegram'

def random(length=10, chars=string.ascii_letters + string.digits):
    return ''.join([choice(chars) for _ in range(length)])

def update(offset):
    respuesta = requests.get(URL + "getUpdates" + "?offset=" + str(offset) + "&timeout=" + str(100))
    mensajes_js = respuesta.content.decode("utf8")
    mensajes_diccionario = json.loads(mensajes_js)
    return mensajes_diccionario

def info_mensaje(mensaje):
    if "photo" in mensaje["message"]:
        tipo = "foto"
    else:
        tipo = "otro"

    persona = mensaje["message"]["from"]["first_name"]
    id_chat = mensaje["message"]["chat"]["id"]
    id_update = mensaje["update_id"]

    return tipo, id_chat, persona, id_update

def descargar_imagen(file_id, file_unique_id, chat_id):
    file_info_url = f'{URL}getFile?file_id={file_id}'
    response = requests.get(file_info_url)

    if response.status_code == 200:
        file_info = response.json()
        file_path = file_info['result']['file_path']

        photo_url = f'https://api.telegram.org/file/bot{TOKEN}/{file_path}'
        photo_response = requests.get(photo_url)

        if photo_response.status_code == 200:
            if not os.path.exists(PHOTO_DIRECTORY):
                os.makedirs(PHOTO_DIRECTORY)

            file_name = f'{chat_id}_{file_unique_id}.jpg'
            file_path = os.path.join(PHOTO_DIRECTORY, file_name)

            with open(file_path, 'wb') as f:
                f.write(photo_response.content)

            return file_name
    return None

def leer_mensaje(mensaje):
    texto = mensaje["message"]["text"]
    return texto

def leer_foto(mensaje, chat_id):
    photo = mensaje["message"]["photo"][-1]
    file_id = photo["file_id"]
    file_unique_id = photo["file_unique_id"]

    downloaded_photo = descargar_imagen(file_id, file_unique_id, chat_id)
    return downloaded_photo

MODEL_PATH = "/content/drive/MyDrive/Modelo/Modelo_densenet201.hdf5"
CLASSES_PATH = "/content/drive/MyDrive/Modelo/clases.json"

model = tf.keras.models.load_model(MODEL_PATH)
with open(CLASSES_PATH, 'r') as f:
    class_names = json.load(f)

def procesar_imagen(photo, chat_id):
    filename = os.path.join(PHOTO_DIRECTORY, photo)

    img = image.load_img(filename, target_size=(256, 256))
    norm_img = image.img_to_array(img) / 255
    input_arr_img = np.array([norm_img])

    probability = model.predict(input_arr_img)[0][0]

    if probability >= 0.5:
        output = "<b>There is no evidence of oral cancer.</b> You can rest assured."
        message = f"<b>Prediction:</b> {output}"
    elif 0.3 < probability < 0.5:
        output = "<b>It is recommended to visit the dentist.</b> It is advisable to have a periodic check-up to be sure."
        accuracy_percentage = 100 - (probability * 100)
        message = f"<b>Prediction:</b> {output}\n<b>Probability of Oral Cancer:</b> {accuracy_percentage:.2f}%"
    else:
        output = "<b>It is advisable to schedule an appointment with the dentist.</b> Professional care can be beneficial for your oral health."
        accuracy_percentage = 100 - (probability * 100)
        message = f"<b>Prediction:</b> {output}\n<b>Probability of Oral Cancer:</b> {accuracy_percentage:.2f}%"


    final_message = f"<b>IA Oral Cancer Chatbot</b>\n\n{message}"

    return final_message

def enviar_mensaje(idchat, texto):

    requests.get(URL + "sendMessage?text=" + texto + "&chat_id=" + str(idchat) + "&parse_mode=HTML")

ultima_id = 0

while True:
    mensajes_diccionario = update(ultima_id)
    for i in mensajes_diccionario.get("result", []):

        tipo, idchat, nombre, id_update = info_mensaje(i)

        if tipo == "foto":
            foto_respuesta = leer_foto(i, idchat)
            texto_respuesta = procesar_imagen(foto_respuesta, idchat)
            enviar_mensaje(idchat, texto_respuesta)
        else:
            texto_respuesta = "This Chatbot Only receives images of the Buccal Cavity"
            enviar_mensaje(idchat, texto_respuesta)

        if id_update > (ultima_id - 1):
            ultima_id = id_update + 1

    mensajes_diccionario = {}