from pygame import mixer
import time,threading
import inspect, os.path
from playsound import playsound


class ReproductorAudio:
    
    def play_audio(self, filename):
        if filename is not None:
            if '.mp3' in filename:
                mixer.music.load(filename)
                mixer.music.play()
            else:
                mixer.Sound(filename).play()
            while mixer.music.get_busy():  # espera que el audio termine de reproducirse
                time.sleep(0.1)
                self.playing = True
            self.playing = False

    def __init__(self):
        filename = inspect.getframeinfo(inspect.currentframe()).filename
        audio_dir= os.path.dirname(os.path.abspath(filename))  + os.sep + 'audio' + os.sep
        self.audio = {
            "billete no identificable": audio_dir + "Billete no identificable.mp3","sumatoria reiniciada": audio_dir +"Sumatoria reiniciada.mp3",
            "50 Pesos":audio_dir +"50 pesos.mp3", "100 Pesos":audio_dir + "100 pesos.mp3", "200 Pesos":audio_dir + "200 pesos.mp3",
            "500 Pesos":audio_dir +"500 pesos.mp3", "1000 Pesos":audio_dir +"1000 pesos.mp3","2000 Pesos": audio_dir + "2000 pesos.mp3",
            "izq_lejos": audio_dir + "izq_lejos.mp3", "izq_cerca": audio_dir + "izq_cerca.mp3", 
            "centro_lejos": audio_dir + "centro_lejos.mp3", "centro_cerca": audio_dir + "centro_cerca.mp3", 
            "der_lejos": audio_dir + "der_lejos.mp3", "der_cerca": audio_dir +"der_cerca.mp3","der_cerca": audio_dir +"der_cerca.mp3",
            "pare": audio_dir +"pare.mp3",
            "0": audio_dir + "Modo obstaculos.mp3", "1": audio_dir + "Modo billetes.mp3", "2": audio_dir +"Modo sumatoria.mp3", "3": audio_dir + "Modo silencio.mp3",
            "encendido": audio_dir +"Encendido.mp3", "apagado": audio_dir +"Apagado.mp3"
        }

        self.playing = False
        mixer.init()
        mixer.set_num_channels(3)
         
    def reproducir(self, key):
        audioFile = self.audio.get(str(key))
        self.play_audio(audioFile)
        """ while (not self.playing):
            if not self.playing:
                hilo = threading.Thread(target=self.play_audio, args=[audioFile], daemon=True)
                hilo.start()
                #playsound(audioFile, block = False)
            else:
                time.sleep(0.2) """
        while (self.playing):
            pass
    
    def reproducir_non_blocking(self, key):
        audioFile = self.audio.get(str(key))
        #hilo = threading.Thread(target=self.play_audio, args=[audioFile], daemon=True)
        #hilo.start()
        mixer.Sound(audioFile).play()
        time.sleep(0.075)
        #playsound(audioFile, block = False)