import pyttsx3
import threading

class Speaker:
    
    def play_audio(self, mensaje):
        self.playing = True
        self.speaker.say(mensaje)
        self.speaker.runAndWait()
        self.playing = False

    def __init__(self):
        self.speaker= pyttsx3.init()
        self.playing = False
        
        #voice_id = 'spanish-latin-am'
        #self.speaker.setProperty('voice', voice_id)
        rate = self.speaker.getProperty('rate')
        self.speaker.setProperty('rate', rate-50)

        #Instalar voces si no hay una en español buena comando: sudo apt-get install espeak
        voices = self.speaker.getProperty('voices')
        self.speaker.setProperty('voice', voices[2].id)

        #Voz en español a utilizar toca verificar en la raspberry si existe o se descarga
        #En pc de windows se descarga en idioma - voces - español mexico
        #self.speaker.setProperty('voice',"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_ES-MX_SABINA_11.0")

    def reproducir(self, mensaje):
        if not self.playing:
            hilo = threading.Thread(target=self.play_audio, args=[mensaje], daemon=True)
            hilo.start()