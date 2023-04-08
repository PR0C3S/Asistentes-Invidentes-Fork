#!/usr/bin/env python

import time, threading
import RPi.GPIO as GPIO
import ReproductorAudio
import objectDetection
import DeteccionBilletes
import math
import cv2
from subprocess import call
from datetime import datetime
import Speaker

BUTTON = 5
debounceSeconds = 0.01
buttonPressedTime = None
shutdownMinSeconds = 3
#GPIO.setmode(GPIO.BCM)

def modo_mute():
    while(MODO[0] == 3):
        time.sleep(0.1) # or pass

def button_callback(pin):
    global stopCondition
    global MODO
    global buttonPressedTime
    
    if not (GPIO.input(pin)):
        if buttonPressedTime is None:
            #buttonPressedTime = datetime.now()
            buttonPressedTime = time.time()
    else:
        if buttonPressedTime is not None:
            #elapsed = (datetime.now() - buttonPressedTime).total_seconds()
            elapsed = time.time() - buttonPressedTime
            buttonPressedTime = None
            if elapsed >= shutdownMinSeconds:
                #button pressed for more than specified time, shutdown
                stopCondition = True
                MODO[0] += 1
            elif elapsed >= debounceSeconds:
                #button pressed for a shorter time, change MODO
                if (MODO[0] + 1) > 3:
                    MODO[0] = 0
                else:
                    MODO[0] += 1
        
# def startButtonDetect:
GPIO.setmode(GPIO.BOARD)
GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(BUTTON, GPIO.BOTH,callback=button_callback)

reproductor = ReproductorAudio.ReproductorAudio()
reproductor.reproducir("encendido")
speaker = Speaker.Speaker()
#speaker.play_audio("Dispositivo encendido")
MODO = [0] #0: objetos, 1: billetes, 2:sumador, 3: mute
stopCondition = False

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

reproductor.reproducir("apagado")
#speaker.play_audio("Apagando dispositivo")
cv2.destroyAllWindows()
time.sleep(3)
call(['shutdown', '-h','now'], shell = False)