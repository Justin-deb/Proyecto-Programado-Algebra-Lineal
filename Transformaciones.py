from PIL import Image,ImageFile
import numpy as np
import math

#Funcion que se encarga de rotar la imagen
def rotateImage(image:Image.Image,angle:int) -> Image.Image:

    #Convertir la imagen en un arreglo
    arrayImage = np.array(image.convert("RGBA"))

    #Requerimos el angulo que esta en grados en radianes
    angleRadians = math.radians(angle)

    #Obtenemos las dimensiones de la imagen
    height,width = arrayImage.shape[:2]

    #Creamos la matriz de rotacion
    rotationMatrix = np.array([
        [math.cos(angleRadians),-math.sin(angleRadians)],
        [math.sin(angleRadians),math.cos(angleRadians)]
    ],dtype=float)

    # #Aplicamos la rotacion a las coordenadas
    # rotatedCoordinates = coordinates @ rotationMatrix

    #Calculamos las dimensiones de la nueva imagen
    corners = np.array([
        [-width/2.0,-height/2.0],
        [width/2.0,-height/2.0],
        [width/2.0,height/2.0],
        [-width/2.0,height/2.0]
    ],dtype=float)

    #Rotamos esquinas (rota las esquinas como vectores columna -> use R @ v)
    rotatedCorners = corners @ rotationMatrix

    #Obtenemos las nuevas dimensiones
    newWidth = int(np.ceil(rotatedCorners[:,0].max() - rotatedCorners[:,0].min()))
    newHeight = int(np.ceil(rotatedCorners[:,1].max() - rotatedCorners[:,1].min()))

    #Creamos las coordenadas a partir de la matriz
    y,x = np.mgrid[:newHeight,:newWidth]

    #Centramos las coordenadas
    xCentered = x - newWidth/2
    yCentered = y - height/2
    
    #Ponemos las coordenadas en un pila
    coordinates = np.stack((xCentered,yCentered),axis=-1)
    
    #Aplicamos rotacion inversa a la matriz de coordenadas
    rotatedCoordinates = coordinates @ rotationMatrix.T

    #Trasladamos de vuelta
    xOffset = rotatedCoordinates[...,0] + width/2
    yOffset = rotatedCoordinates[...,1] + height/2

    #Creamos una variable que almacenes las coordenadas validas
    validMask = (
        (xOffset >= 0) & (xOffset < width) &
        (yOffset >= 0) & (yOffset < height)
    )

    #Empezamos a crear el arreglo con el resultado final
    result = np.zeros((newHeight,newWidth,4),dtype=np.uint8)

    #Convertimos las coordenadas en numeros enteros para poder usarlos como indices
    xOffset = xOffset.astype(np.int32)
    yOffset = yOffset.astype(np.int32)

    #Copiamos los pixeles validos
    result[validMask] = arrayImage[yOffset[validMask],xOffset[validMask]]

    #Convertimos a una imagen y lo devolvemos
    return Image.fromarray(result)