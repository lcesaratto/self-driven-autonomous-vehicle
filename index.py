import cv2
import numpy as np
from pyzbar import pyzbar
# from MLfunctions import *
import matplotlib.pyplot as plt
import statistics

class SeguimientoLineas (object):
    def __init__(self):
        self.cap = self._abrirCamara()
        self.fps, self.width, self.height = self._obtenerParametrosFrame()

        # self.count=0
        self.bocacalle=False
        self.right_points_up_arr = np.zeros(10)
        self.left_points_up_arr = np.zeros(10)
        self.right_points_up_med = 0
        self.left_points_up_med = 0
        # # Array para almacenar las ultimas 10 posiciones del vehiculo
        self.ultimas_posiciones = np.zeros(10)
        self.indice_ultima_posicion = 0

        self.activar_linea_vertical = False
        self.ultimas_posiciones_derecha = np.zeros(10)
        self.indice_doblar_derecha = 0
        self.activar_doblar_derecha = False
        self.ultimas_posiciones_izquierda = np.zeros(10)
        self.indice_doblar_izquierda = 0
        self.activar_doblar_izquierda = False

        self.indice_ultima_posicion_2 = 0

        self.right_points_up = np.array([0, 0])
        self.left_points_up = np.array([0, 0])
        self.right_points_up_2 = np.array([0, 0])
        self.left_points_up_2 = np.array([0, 0])
        
    def _abrirCamara (self):
        # Create a VideoCapture object and read from input file
        # If the input is the camera, pass 0 instead of the video file name
        cap = cv2.VideoCapture('Videos/20191012_213614.mp4')#('Videos/WhatsApp Video 2019-10-12 at 6.19.29 PM(2).mp4')
        # Check if camera opened successfully
        if not cap.isOpened():
            print("Error opening video stream or file")
        return cap

    def _obtenerParametrosFrame(self):
        fps =  self.cap.get(cv2.CAP_PROP_FPS)
        width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH )
        height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        return fps, width, height

    def _prepararFrame (self, frame):
        # frame = cv2.flip(frame, flipCode=-1)
        frame = frame[0:int(self.height*0.5),0:int(self.width)]
        return frame

    def _aplicarFiltrosMascaras (self, frame):
        #Defino parametros HLS o HSV para detectar solo lineas negras 
        lower_black = np.array([0, 0, 0]) #108 6 17     40 16 37
        upper_black = np.array([150, 75, 255]) #HSV 255, 255, 90 #HLS[150, 75, 255]

        #Aplico filtro de color con los parametros ya definidos
        # hsv_right = cv2.cvtColor(frame, cv2.COLOR_BGR2HLS) #BRG2HLS
        hsv_right = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV) #BRG2HLS
        # cv2.imshow('framefilterHSV', hsv_right)
        mask_right = cv2.inRange(frame, lower_black, upper_black)
        res_right = cv2.bitwise_and(frame, frame, mask=mask_right)
        # cv2.imshow('framefilter', res_right)

        #Aplico filtro pasa bajos y deteccion de lineas por Canny
        '''
        kernel = np.ones((3,3), np.uint8)
        frame_e = cv2.erode(frame, kernel, iterations=1)
        gray_right = cv2.cvtColor(frame_e, cv2.COLOR_BGR2GRAY) 
        (thresh, bw_right) = cv2.threshold(gray_right, 40, 255, cv2.THRESH_BINARY)
        #dif_gray_right = cv2.GaussianBlur(bw_right, (1, 1), 0) #(mask, (5, 5), 0)
        cv2.imshow('framefilterdif', frame_e)
        canny_right = cv2.Canny(bw_right, 25, 175) # 25, 175)
        cv2.imshow('framefilter', canny_right)
        '''
        #Umbral Dinamico
        kernel = np.ones((3,3), np.uint8)
        frame_e = cv2.erode(frame, kernel, iterations=1)
        gray = cv2.cvtColor(frame_e, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        gray = cv2.medianBlur(gray, 5)
        dst2 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 9, 5)
        # cv2.imshow('framefilterdif', dst2)
        dif_gray_right = cv2.GaussianBlur(dst2, (11, 11), 0) #(mask, (5, 5), 0)
        #cv2.imshow('framefilterdif', frame_e)
        canny_right = cv2.Canny(dif_gray_right, 25, 175) # 25, 175)
        kernel = np.ones((7,7), np.uint8)
        canny_right = cv2.morphologyEx(canny_right, cv2.MORPH_CLOSE, kernel)
        kernel = np.ones((3,3), np.uint8)
        canny_right = cv2.erode(canny_right, kernel, iterations=1)
        # cv2.imshow('framefilter', canny_right)
        return canny_right

    def _obtenerPorcionesFrame (self, frameOriginal, frame, row, column):
        frameCut=frame[(200-row*40):(240-row*40),(40*column):(40+40*column)]
        frameOriginalCut=frameOriginal[(200-row*40):(240-row*40),(40*column):(40+40*column)]
        return frameCut, frameOriginalCut

    def _procesarPorcionFrame (self, cannyCut, frameCut, fila, columna):

        try:
            # frameCut = canny_right
            ## Aplico Transformada de Hough
            lines = cv2.HoughLinesP(cannyCut, 1, np.pi / 180, 10, minLineLength=0, maxLineGap=1) #(canny, 1, np.pi / 180, 30, minLineLength=15, maxLineGap=150)

            # Draw lines on the image
            if lines is not None:
                cant_lineas=len(lines)
                # print(cant_lineas)
                
                if cant_lineas>100: # print('Se detecto una curva')
                    frameCut[:,:,2] = frameCut[:,:,2] + 50
                else: # print('Se detecto una linea')
                    x1M=0
                    x1M_2=0


                    for line in lines:
                        x1, y1, x2, y2 = line[0]

                        if(x1>x1M and fila==2):
                            x1M=x1
                            self.right_points_up = [x1+40*columna, y1+40*(5-fila)]
                            self.right_points_down = [x2, y2]
                        if(columna<7 and fila==2):
                            # print(x1+40*column)
                            self.left_points_up = [x1+40*columna, y1+40*(5-fila)]
                            self.left_points_down = [x2, y2]
                        if(x1>x1M_2 and fila==5):
                            x1M_2=x1
                            self.right_points_up_2 = [x1+40*columna, y1+40*(5-fila)]
                            self.right_points_down_2 = [x2, y2]
                        if(columna<7 and fila==5):
                            # print(x1+40*column)
                            self.left_points_up_2 = [x1+40*columna, y1+40*(5-fila)]
                            self.left_points_down_2 = [x2, y2]    
                        # x1m=x1
                        # right_points = [(x1,y1), (x2,y2)]

                        cv2.line(frameCut,(x1,y1),(x2,y2),(0,0,255),2)
                        # cv2.line(frameCut,(frameCut.shape[1]-1,x1),(0,y1),255,2)

                    frameCut[:,:,0] = frameCut[:,:,0]+50
            else:
                frameCut[:,:,1] = frameCut[:,:,1] + 50        

        except Exception as e:
            print(e)
        return frameCut

    def run (self):
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frameOriginal = self._prepararFrame(frame)
                frame = self._aplicarFiltrosMascaras(frameOriginal)
                filasDeseadas = [2, 5]
                columnasDeseadas = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
                frameProcesado = frameOriginal
                for fila in filasDeseadas: #Recorre de abajo para arriba, de izquierda a derecha
                    for columna in columnasDeseadas:
                        porcionFrame, porcionFrameOriginal = self._obtenerPorcionesFrame(frameOriginal, frame, fila, columna)
                        porcionFrameProcesado = self._procesarPorcionFrame(porcionFrame, porcionFrameOriginal, fila, columna)
                        for x in range(40): #filas
                            for j in range(40): #columnas
                                # print(frameCut[x][j])
                                frameProcesado[200-fila*40+x][0+40*columna+j] = porcionFrameProcesado[x][j]

                # if (frame == frameResulting).all(): #Esto es para verificar que el frame original sea igual al reconstruido
                # print ("Excelente!")


                if self.bocacalle:
                    cv2.line(frameProcesado,(left_points_up_last,140),(right_points_up_last,140),(0,255,0),2)
                else:
                    cv2.line(frameProcesado,(self.left_points_up[0],140),(self.right_points_up[0],140),(255,255,255),2)
                
                cv2.line(frameProcesado,(self.left_points_up_2[0],20),(self.right_points_up_2[0],20),(255,255,255),2)
                dist_line_down = self.right_points_up[0] - self.left_points_up[0]
                dist_line_up = self.right_points_up_2[0] - self.left_points_up_2[0]
                    
                
                if ((dist_line_down > 200)): #En promedio 170 # or dist_line_down < 150
                    if not self.bocacalle:
                        right_points_up_last = int(statistics.median(self.right_points_up_arr))
                        left_points_up_last = int(statistics.median(self.left_points_up_arr))
                    self.bocacalle=True
                else:
                    if (self.indice_ultima_posicion_2 is 10):
                        self.indice_ultima_posicion_2 = 0
                    self.right_points_up_arr[self.indice_ultima_posicion_2] = self.right_points_up[0]
                    self.left_points_up_arr[self.indice_ultima_posicion_2] = self.left_points_up[0]
                    self.right_points_up_med = int(statistics.median(self.right_points_up_arr))
                    self.left_points_up_med = int(statistics.median(self.left_points_up_arr))
                    self.indice_ultima_posicion_2 += 1
                    if ((self.right_points_up_med*0.9 < self.right_points_up[0] < self.right_points_up_med*1.1) and (self.left_points_up_med*0.9 < self.left_points_up[0] < self.left_points_up_med*1.1)):
                        self.bocacalle=False

                if self.activar_doblar_derecha:
                    if (not (statistics.median(self.ultimas_posiciones_derecha)*0.8 <= self.right_points_up[0] <= 
                    statistics.median(self.ultimas_posiciones_derecha)*1.2)) and (statistics.median(self.ultimas_posiciones_izquierda)*0.8 <= 
                    self.left_points_up[0] <= statistics.median(self.ultimas_posiciones_izquierda)*1.2):
                        self.activar_linea_vertical = True
                        self.activar_doblar_derecha = False
                        self.ultimas_posiciones_final = self.ultimas_posiciones
                        last = int(statistics.median(self.ultimas_posiciones_final))

                if (self.indice_ultima_posicion is 10):
                    self.indice_ultima_posicion = 0
                self.ultimas_posiciones[self.indice_ultima_posicion] = (self.left_points_up[0]+self.right_points_up[0])/2
                self.indice_ultima_posicion += 1

                if (self.indice_doblar_derecha is 10):
                    self.indice_doblar_derecha = 0
                self.ultimas_posiciones_derecha[self.indice_doblar_derecha] = self.right_points_up[0]
                self.indice_doblar_derecha += 1

                if (self.indice_doblar_izquierda is 10):
                    self.indice_doblar_izquierda = 0
                self.ultimas_posiciones_izquierda[self.indice_doblar_izquierda] = self.left_points_up[0]
                self.indice_doblar_izquierda += 1

                
                if self.activar_linea_vertical:
                    cv2.line(frameProcesado,(last,0),(last,320),(255,255,255),2)

                # Grid lines at these intervals (in pixels)
                # dx and dy can be different
                dx, dy = 40,40
                # Custom (rgb) grid color
                grid_color = [255,0,0]# [0,0,0]
                # Modify the image to include the grid
                frameProcesado[:,::dy,:] = grid_color
                frameProcesado[::dx,:,:] = grid_color

                # Display the resulting frame
                cv2.imshow('frameResulting', frameProcesado)

                # Press Q on keyboard to  exit
                key = cv2.waitKey(10)
                if key == ord('q'):  # 25fps
                    break
                elif key == ord('k'):
                    self.activar_doblar_derecha = True
            
            else: # Break the loop
                break

        # When everything done, release the video capture object
        self.cap.release()
        # Closes all the frames
        cv2.destroyAllWindows()

def qr_reader():

    img_path = 'image.jpg'

    img = cv2.imread(img_path)

    barcodes = pyzbar.decode(img)

    for barcode in barcodes:
        (x, y, w, h) = barcode.rect
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)
        barcodeData = barcode.data.decode("utf-8")
        barcodeType = barcode.type
        text = "{} ({})".format(barcodeData, barcodeType)
        cv2.putText(img, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        print("[INFO] found {} barcode {}".format(barcodeType, barcodeData))
    cv2.imwrite("new_img.jpg", img)
            
if __name__ == "__main__":
    # qr_reader()
    # Image = cv2.imread('airplane.jpeg')
    # print(Image)
    # predict_cifar10(Image)
    seguidorLineas = SeguimientoLineas()
    seguidorLineas.run()