import cv2
import os
import ReproductorAudio
import depthai as dai
import inspect, os.path
from time import time
import shutil
import Speaker

class DeteccionBilletes:
    
    def __init__(self, reproductor, speaker):
        self.reproductor = reproductor

        #SUMADOR BILLETES
        self.speaker = speaker
        self.totalSumado = 0
        self.timeLastDetect = None
        self.lastDetect = None
        self.lastTimeDetect = time()
        self.contador = 0
        
        #ORB setup
        self.orb = cv2.ORB_create()
        filename = inspect.getframeinfo(inspect.currentframe()).filename
        self.path = os.path.dirname(os.path.abspath(filename)) + os.sep + 'Billetes Dataset' 
        self.images = []
        self.classNames = []
        
        for imageName in os.listdir(self.path):
            impath = self.path + os.sep + imageName
            currentImage = cv2.imread(impath, cv2.IMREAD_GRAYSCALE)
            if currentImage is None:
                shutil.copy(impath, imageName)
                currentImage = cv2.imread(imageName)
                os.remove(imageName)
            self.images.append(currentImage)
            self.classNames.append(os.path.splitext(imageName)[0])

        self.desList = self.findDescriptors(self.images)
        
    def findDescriptors(self, images):
        desList=[]
        for img in images:
            kp,des = self.orb.detectAndCompute(img,None)
            desList.append(des)
        return desList

    def findID(self, img, thres=25):
        kp2,des2 = self.orb.detectAndCompute(img, None)  
        FLANN_INDEX_LSH = 6
        index_params= dict(algorithm = FLANN_INDEX_LSH,
                    table_number = 6, # 12
                    key_size = 12,     # 20
                    multi_probe_level = 1) #2
        search_params = dict(checks=70)   # or pass empty dictionary               
        flann = cv2.FlannBasedMatcher(index_params,search_params)
        
        matchList = []
        nombreBillete = ""
        try:
            for des in self.desList:
                matches = flann.knnMatch(des,des2,k=2)
                good = []
                for m,n in matches:
                    if m.distance < 0.75 * n.distance:
                        good.append(m)
                matchList.append(len(good))
        except:
            pass
        if len(matchList)> 0:
            if max(matchList) >= thres:
                id = matchList.index(max(matchList))
                nombreBillete = self.classNames[id]
                nombreBillete = nombreBillete.split("_")
                nombreBillete = nombreBillete[0]
            """ else:
                if( max(matchList)>5):
                    nombreBillete = "billete no identificable" """
        return nombreBillete
      
    
    def sumadorBilletes(self, billete):
        actualTime = time()
        if self.lastDetect == None:
            self.timeLastDetect = actualTime

        if (actualTime-self.timeLastDetect) > 30:
            self.speaker.play_audio(f"Total reiniciado")
            self.lastDetect = None
            self.totalSumado = 0
            
        if(billete == self.lastDetect and (actualTime-self.timeLastDetect) < 5):
           return
        else:
            self.timeLastDetect = actualTime
            self.lastDetect = billete
            self.totalSumado += int(billete)
            self.speaker.reproducir(f"Total actual es {self.totalSumado} Pesos")
              
    def __call__(self, MODO):
        
        #camera pipeline setup
        pipeline = dai.Pipeline()
        
        cam_rgb = pipeline.createColorCamera()
        #cam_rgb = pipeline.create(dai.node.MonoCamera)
        #camRgb = pipeline.create(dai.node.ColorCamera)
        
        xout_rgb = pipeline.createXLinkOut()
        #xoutVideo = pipeline.create(dai.node.XLinkOut)
        
        xout_rgb.setStreamName("rgb")
        #xoutVideo.setStreamName("video")
        
        cam_rgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        #cam_rgb.setIspScale(2, 3)  # Devide both width/heigth by 2/3
        cam_rgb.setPreviewSize(640, 480)
        #cam_rgb.setPreviewSize(704, 528)
        #cam_rgb.setPreviewSize(300, 300)
        cam_rgb.setInterleaved(True)
        cam_rgb.setBoardSocket(dai.CameraBoardSocket.AUTO)
        #cam_rgb.setVideoSize(640,480)
        
        #xoutVideo.input.setBlocking(False)
        #xoutVideo.input.setQueueSize(1)
        
        cam_rgb.preview.link(xout_rgb.input)
        #cam_rgb.video.link(xoutVideo.input)
        
        device = dai.Device(pipeline, usb2Mode=True)
        q_rgb = device.getOutputQueue("rgb", maxSize=4, blocking=False)
        #video = device.getOutputQueue(name="video", maxSize=1, blocking=False)
        frame = None
        
        #PARA EL CUADRADO
        """anchocam, altocam = 640,480 #dimension de la camara
        mitad = int(anchocam) #Tamo de la mitad del ancho de la camara
        cuadro = 100 #Dimension a eliminar
        """
        while (MODO[0] == 2):
            in_rgb = q_rgb.get()
            frame = in_rgb.getCvFrame()
            frame = cv2.cvtColor(frame,cv2.IMREAD_GRAYSCALE)
            #cuadrado
            """cv2.rectangle(frame, (cuadro, cuadro), (mitad - cuadro, altocam - cuadro), (0,0,0,0) ,2) #Generamos el cuadro
            ox1, oy1 = cuadro, cuadro 
            ancho1, alto1 = (mitad - cuadro) - ox1, (altocam - cuadro) - oy1 #REliminamos el area que no deseamos
            ox2, oy2 = ox1 + ancho1, oy1 + alto1 #REliminamos el area que no deseamos
            objeto = frame[oy1:oy2,ox1:ox2] #Tomamos los datos del frame a utilizar
            """
            nombreBillete = self.findID(frame)
            #nombreBillete = self.findID(objeto)
            if nombreBillete:
                nombreBillete = nombreBillete = nombreBillete.split(" ")
                nombreBillete = nombreBillete[0]
                self.sumadorBilletes(nombreBillete)
            cv2.imshow('Sumador billetes',frame)
            cv2.waitKey(1)
            
        while (MODO[0] == 1):
            in_rgb = q_rgb.get()
            frame = in_rgb.getCvFrame()
            frame = cv2.cvtColor(frame,cv2.IMREAD_GRAYSCALE)
            #cuadrado
            """cv2.rectangle(frame, (cuadro, cuadro), (mitad - cuadro, altocam - cuadro), (0,0,0,0) ,2) #Generamos el cuadro
            ox1, oy1 = cuadro, cuadro 
            ancho1, alto1 = (mitad - cuadro) - ox1, (altocam - cuadro) - oy1 #REliminamos el area que no deseamos
            ox2, oy2 = ox1 + ancho1, oy1 + alto1 #REliminamos el area que no deseamos
            objeto = frame[oy1:oy2,ox1:ox2] #Tomamos los datos del frame a utilizar
            """
            #nombreBillete = self.findID(objeto)
            nombreBillete = self.findID(frame)
            if nombreBillete:
                tiempoTotal = time()-self.lastTimeDetect
                print(f"Billete: {nombreBillete}, Duracion entre ultima deteccion: {tiempoTotal}, intento: {self.contador}")
                #self.speaker.reproducir(str(nombreBillete))
                self.contador= self.contador +1
                self.reproductor.reproducir(nombreBillete)
                self.lastTimeDetect = time()
            cv2.imshow('Deteccion Billetes',frame)
            if cv2.waitKey(1) == ord('e'):
                    break
        #frame.release()
        cv2.destroyAllWindows()
