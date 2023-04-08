from pathlib import Path
import sys
import cv2
import depthai as dai
import numpy as np
import time
import argparse
import json
import blobconverter
import ReproductorAudio
import inspect, os.path
import math


accept = {"person", 0,
            "bicycle",1,
            "car",2,
            "motorbike",3,
            "aeroplane",
            "bus",5,
            "train",6,
            "truck",7,
            "fire hydrant",10,
            "stop sign",11,
            "parking meter",12,
            "bench",13,
            "sheep",18,
            "cow",19,
            "chair",56,
            "sofa",57,
            "pottedplant",58,
            "bed",59,
            "diningtable",60,
            "toilet",61,
            "oven",69,
            "refrigerator",72,
            }

cooldownCounter = 0
testIgnore = {"person",1,0}

def determine_label(det):
    #print(det.label)
    if det.label in accept:
        return True
    else:
        return False

def filter_detections(detections):
    #detections[:] = [x for x in detections if  determine_label(x)]
    #detections = [x for x in detections if not determine_label(x)]
    left_closest = None
    center_closest = None
    right_closest = None
    for det in detections:
        X = det.spatialCoordinates.x
        Z = det.spatialCoordinates.z
        
        if determine_label(det):
        
            if (X < -150):
                if (left_closest == None) or (Z < left_closest.spatialCoordinates.z):
                    left_closest = det
                    
            elif (X < 150):
                if (center_closest == None) or (Z < center_closest.spatialCoordinates.z):
                    center_closest = det

            else:
                if (right_closest == None) or (Z < right_closest.spatialCoordinates.z):
                    right_closest = det
    
    temp = []
    if (left_closest != None):
        temp.append(left_closest)
    if (center_closest != None):
        temp.append(center_closest)
    if (right_closest != None):
        temp.append(right_closest)
    return temp
    
def sound_coordenates(reproductor, detections):
    global cooldownCounter
    now = time.time()
    if now >= cooldownCounter:
        cooldownCounter = time.time() + 2
        for det in detections:
            X = det.spatialCoordinates.x
            Z = det.spatialCoordinates.z
            
            if (X < -150):
                if Z < 2000:
                    reproductor.reproducir_non_blocking("izq_cerca")
                    print("izq cerca")
                else :
                    print("izq lejos")
                    reproductor.reproducir_non_blocking("izq_lejos")
                    
            elif X < 150:
                if Z < 2000:
                    print("centro cerca")
                    reproductor.reproducir_non_blocking("centro_cerca")
                else :
                    print("centro lejos")
                    reproductor.reproducir_non_blocking("centro_lejos")
            else:
                if Z < 2000:
                    print("der cerca")
                    reproductor.reproducir_non_blocking("der_cerca")
                else :
                    print("der lejos")
                    reproductor.reproducir_non_blocking("der_lejos")
        
                #print("X = " + str(X))
                #print("Z = "+ str(Z))
    
class ObjectDetection:
    
    def __init__(self, reproductor):
        self.reproductor = reproductor
        
        
    def __call__(self, MODO):
        
        # parsear argumentos
        filename = inspect.getframeinfo(inspect.currentframe()).filename
        path     = os.path.dirname(os.path.abspath(filename))
        parser = argparse.ArgumentParser()
        parser.add_argument("-m", "--model", help="Provide model name or model path for inference",
                            default=path + '/yolov5n_coco_416x416_openvino_2021.4_6shave.blob', type=str)
        parser.add_argument("-c", "--config", help="Provide config path for inference",
                            default=path + '/json/yolov5.json', type=str)
        args = parser.parse_args()

        # parsear configuracion
        configPath = Path(args.config)
        if not configPath.exists():
            raise ValueError("Path {} does not exist!".format(configPath))

        with configPath.open() as f:
            config = json.load(f)
        nnConfig = config.get("nn_config", {})

        # parsear forma entrada
        if "input_size" in nnConfig:
            W, H = tuple(map(int, nnConfig.get("input_size").split('x')))

        # extraer metadata
        metadata = nnConfig.get("NN_specific_metadata", {})
        classes = metadata.get("classes", {})
        coordinates = metadata.get("coordinates", {})
        anchors = metadata.get("anchors", {})
        anchorMasks = metadata.get("anchor_masks", {})
        iouThreshold = metadata.get("iou_threshold", {})
        confidenceThreshold = metadata.get("confidence_threshold", {})

        # parsear labels
        #nnMappings = config.get("mappings", {})
        #labels = nnMappings.get("labels", {})
         
        # get model path
        nnPath = args.model
        if not Path(nnPath).exists():
            print("No blob found at {}. Looking into DepthAI model zoo.".format(nnPath))
            nnPath = str(blobconverter.from_zoo(args.model, shaves = 6, zoo_type = "depthai", use_cache=True))
        # sync outputs
        syncNN = True

        # Crear pipeline
        pipeline = dai.Pipeline()

        # Definicion fuentes y salidas
        camRgb = pipeline.create(dai.node.ColorCamera)
        spatialDetectionNetwork = pipeline.create(dai.node.YoloSpatialDetectionNetwork)
        monoLeft = pipeline.create(dai.node.MonoCamera)
        monoRight = pipeline.create(dai.node.MonoCamera)
        stereo = pipeline.create(dai.node.StereoDepth)
        #nnNetworkOut = pipeline.create(dai.node.XLinkOut)
        manip = pipeline.create(dai.node.ImageManip)

        xoutRgb = pipeline.create(dai.node.XLinkOut)
        xoutNN = pipeline.create(dai.node.XLinkOut)
        xoutBoundingBoxDepthMapping = pipeline.create(dai.node.XLinkOut)
        xoutDepth = pipeline.create(dai.node.XLinkOut)

        #nnNetworkOut.setStreamName("nnNetwork")
        xoutRgb.setStreamName("rgb")
        xoutNN.setStreamName("detections")
        xoutBoundingBoxDepthMapping.setStreamName("boundingBoxDepthMapping")
        xoutDepth.setStreamName("depth")

        # Propiedades
        #camRgb.setPreviewSize(W, H)
        #camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        camRgb.setInterleaved(False)
        camRgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
        #camRgb.setFps(40)
        
        ##
        camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_12_MP)
        camRgb.setIspScale(1,5) # 4056x3040 -> 812x608
        camRgb.setPreviewSize(812, 608)
        camRgb.setFps(25)
        
        
        # Use ImageManip to resize to 300x300 with letterboxing
        manip.setResize(416,416)
        manip.setMaxOutputFrameSize(519168) # 300x300x3 = 270000
        #letterboxing
        manip.initialConfig.setResizeThumbnail(416,416)
        #stertching
        #manip.initialConfig.setKeepAspectRatio(False) # Stretching the image
       
        #xoutIsp = pipeline.create(dai.node.XLinkOut)
        #xoutIsp.setStreamName("isp")
        #camRgb.isp.link(xoutIsp.input)

        monoLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
        monoLeft.setBoardSocket(dai.CameraBoardSocket.LEFT)
        monoRight.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
        monoRight.setBoardSocket(dai.CameraBoardSocket.RIGHT)

        # setting node configs 
        stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
        # Alineacion de mapa de profundidad a la perspectiva de la camara RGB
        stereo.setDepthAlign(dai.CameraBoardSocket.RGB)
        stereo.setOutputSize(monoLeft.getResolutionWidth(), monoLeft.getResolutionHeight())

        """
        spatialDetectionNetwork.setBoundingBoxScaleFactor(0.5)
        spatialDetectionNetwork.setDepthLowerThreshold(100)
        spatialDetectionNetwork.setDepthUpperThreshold(5000) 
        """

        #Parametros red neuronal
        spatialDetectionNetwork.setConfidenceThreshold(confidenceThreshold)
        spatialDetectionNetwork.setNumClasses(classes)
        spatialDetectionNetwork.setCoordinateSize(coordinates)
        spatialDetectionNetwork.setAnchors(anchors)
        spatialDetectionNetwork.setAnchorMasks(anchorMasks)
        spatialDetectionNetwork.setIouThreshold(iouThreshold)
        spatialDetectionNetwork.setBlobPath(nnPath)
        spatialDetectionNetwork.input.setBlocking(False)
        
        spatialDetectionNetwork.setNumInferenceThreads(2)
        #spatialDetectionNetwork.setNumNCEPerInferenceThread(1)
        spatialDetectionNetwork.input.setQueueSize(1)
        

        # Linking
        camRgb.preview.link(manip.inputImage)
        #camRgb.preview.link(spatialDetectionNetwork.input)
        manip.out.link(spatialDetectionNetwork.input)
        spatialDetectionNetwork.out.link(xoutNN.input)
        if syncNN:
            spatialDetectionNetwork.passthrough.link(xoutRgb.input)
        else:
            camRgb.preview.link(xoutRgb.input)
            #camRgb.preview.link(xoutIsp.input)

        
        monoLeft.out.link(stereo.left)
        monoRight.out.link(stereo.right)
        spatialDetectionNetwork.boundingBoxMapping.link(xoutBoundingBoxDepthMapping.input)
        stereo.depth.link(spatialDetectionNetwork.inputDepth)
        spatialDetectionNetwork.passthroughDepth.link(xoutDepth.input)
        #spatialDetectionNetwork.outNetwork.link(nnNetworkOut.input)

        #  Conecta a dispositivo e inicializa pipeline
        with dai.Device(pipeline) as device:
            
            # Colas de salida seran usadas para obtener frames rgb y data de red neuronal de las salidas definidas arriba
            previewQueue = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
            detectionNNQueue = device.getOutputQueue(name="detections", maxSize=4, blocking=False)
            xoutBoundingBoxDepthMappingQueue = device.getOutputQueue(name="boundingBoxDepthMapping", maxSize=4, blocking=False)
            depthQueue = device.getOutputQueue(name="depth", maxSize=4, blocking=False)
            #networkQueue = device.getOutputQueue(name="nnNetwork", maxSize=4, blocking=False)
            #qIsp = device.getOutputQueue(name='isp')

            startTime = time.monotonic()
            counter = 0
            fps = 0
            color = (255, 255, 255)

            while (MODO[0] == 0):
                inPreview = previewQueue.get()
                #inIsp = qIsp.get()
                inDet = detectionNNQueue.get()
                depth = depthQueue.get()
                #inNN = networkQueue.get()

                frame = inPreview.getCvFrame()
                #frame = inIsp.getCvFrame()
                depthFrame = depth.getFrame() # valores depthFrame son en milimetros

                depthFrameColor = cv2.normalize(depthFrame, None, 255, 0, cv2.NORM_INF, cv2.CV_8UC1)
                depthFrameColor = cv2.equalizeHist(depthFrameColor)
                depthFrameColor = cv2.applyColorMap(depthFrameColor, cv2.COLORMAP_HOT)

                counter+=1
                current_time = time.monotonic()
                if (current_time - startTime) > 1 :
                    fps = counter / (current_time - startTime)
                    counter = 0
                    startTime = current_time

                detections = inDet.detections
                if len(detections) != 0:
                    
                    detections = filter_detections(detections)
                    sound_coordenates(self.reproductor, detections)
                    
                    #detections = filter(determine_label, detections) #returns iterator.. might have to cast it back to list with list()
                    
                    boundingBoxMapping = xoutBoundingBoxDepthMappingQueue.get()
                    roiDatas = boundingBoxMapping.getConfigData()

                    for roiData in roiDatas:
                        roi = roiData.roi
                        roi = roi.denormalize(depthFrameColor.shape[1], depthFrameColor.shape[0])
                        topLeft = roi.topLeft()
                        bottomRight = roi.bottomRight()
                        xmin = int(topLeft.x)
                        ymin = int(topLeft.y)
                        xmax = int(bottomRight.x)
                        ymax = int(bottomRight.y)

                        cv2.rectangle(depthFrameColor, (xmin, ymin), (xmax, ymax), color, cv2.FONT_HERSHEY_SCRIPT_SIMPLEX)


                # Si el frame esta disponible, traza caja delimitante en el y lo muestra.
                height = frame.shape[0]
                width  = frame.shape[1]
                for detection in detections:
                    
                    # Denormalize bounding box
                    x1 = int(detection.xmin * width)
                    x2 = int(detection.xmax * width)
                    y1 = int(detection.ymin * height)
                    y2 = int(detection.ymax * height)
                    try:
                        label = labelMap[detection.label]
                    except:
                        label = detection.label
                    cv2.putText(frame, str(label), (x1 + 10, y1 + 20), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
                    cv2.putText(frame, "{:.2f}".format(detection.confidence*100), (x1 + 10, y1 + 35), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
                    cv2.putText(frame, f"X: {int(detection.spatialCoordinates.x)} mm", (x1 + 10, y1 + 50), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
                    cv2.putText(frame, f"Y: {int(detection.spatialCoordinates.y)} mm", (x1 + 10, y1 + 65), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)
                    cv2.putText(frame, f"Z: {int(detection.spatialCoordinates.z)} mm", (x1 + 10, y1 + 80), cv2.FONT_HERSHEY_TRIPLEX, 0.5, 255)

                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, cv2.FONT_HERSHEY_SIMPLEX)

                cv2.putText(frame, "NN fps: {:.2f}".format(fps), (2, frame.shape[0] - 4), cv2.FONT_HERSHEY_TRIPLEX, 0.4, color)
                cv2.imshow("depth", depthFrameColor)
                cv2.imshow("rgb", frame)

                if cv2.waitKey(1) == ord('e'):
                    break
            cv2.destroyAllWindows()