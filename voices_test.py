import pyttsx3

speaker= pyttsx3.init()
voice_id = 'spanish-latin-am'
speaker.setProperty('voice', voice_id)
speaker.setProperty('rate', 150)

#Para buscar las voces
#Instalar voces si no hay una en español buena comando: sudo apt-get install espeak
voices = speaker.getProperty('voices')
for voice in voices:
    speaker.say("Probando voces instaladas")
    speaker.setProperty('voice', voice.id)
    print(voice.id)
    speaker.runAndWait()