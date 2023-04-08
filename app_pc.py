from pynput.keyboard import Key, Listener
from time import time, sleep
import threading
import ReproductorAudio
import objectDetection
import DeteccionBilletes
import cv2
import Speaker


def modo_mute():
    while(MODO[0] == 3):
        sleep(0.1) # or pass

def on_press(key):
    global pressed_since
    global last_pressed
    if hasattr(key, 'char'):
        if (key != None) and (key.char.upper() == 'Q') and (key != last_pressed):
            pressed_since = time()
            last_pressed = key
    
def on_release(key):
    global pressed_since
    global stopCondition
    global last_pressed
    global MODO
    last_pressed = None
    if hasattr(key, 'char') and key.char.upper() == 'Q':
        if (time() - pressed_since) > 2:
            MODO[0] = 999
            stopCondition = True
            #pressed_since = math.inf
        else:
            if (MODO[0] + 1) > 3:
                MODO[0] = 0
            else:
                MODO[0] += 1

reproductor = ReproductorAudio.ReproductorAudio()
reproductor.reproducir("encendido")
speaker = Speaker.Speaker()
#speaker.play_audio("Dispositivo encendido")
#MODO = 0 #0: objetos, 1: billetes, 2:Mute
MODO = [0]
stopCondition = False
last_pressed = None
listener = Listener(on_press=on_press, on_release=on_release)
listener.start()


while (not stopCondition):
    if MODO[0] == 0:
        #speaker.reproducir("Modo deteccion de obstaculos")
        reproductor.reproducir("0")
        detectorObjetos = objectDetection.ObjectDetection(reproductor)
        detectorObjetos(MODO)
    elif MODO[0] == 1:
        #speaker.reproducir("Modo deteccion de billetes")
        reproductor.reproducir("1")
        detectorBilletes = DeteccionBilletes.DeteccionBilletes(reproductor, speaker)
        #detectorBilletes = DeteccionBilletes.DeteccionBilletes(reproductor)
        detectorBilletes(MODO)
    elif MODO[0] == 2:
        reproductor.reproducir("2")
        #speaker.reproducir("Modo sumador de billetes")
        detectorBilletes = DeteccionBilletes.DeteccionBilletes(reproductor, speaker, True)
        detectorBilletes(MODO)
    elif MODO[0] == 3:
        #speaker.reproducir("Modo silencio")
        reproductor.reproducir("3")
        modo_mute()

reproductor.play_audio("audio\Apagado.mp3")
#speaker.play_audio("Apagando dispositivo")
cv2.destroyAllWindows()