from customtkinter import *
from PIL import Image
import Transformaciones
import ObjectDetection as OD

#Funcion encargada de cargar las imagenes de la computadora en una lista
def loadImages():
    try:
        listImages = ["./Resources/Image1.png","./Resources/Image2.png","./Resources/Image3.png"]
        return listImages
    except:
        print("Images not founded")
        return []

#crea la instancia de Custom Tkinter(GUI)
app = CTk()

images = loadImages()

secondaryFrame = CTkFrame(master=app,fg_color="transparent")
secondaryFrame.pack(expand=True,fill="both")

#Funcion se encarga de crear la pantalla, configurarla y centrarla
def createWindow(parent:CTk, width:int, height:int):
    global screenWidth, screenHeight 
    screenWidth = (parent.winfo_screenwidth()//2)-(width//2)
    screenHeight = (parent.winfo_screenheight()//2)-(height//2)


    app.geometry(f"{width}x{height}+{screenWidth}+{screenHeight}")#crea la pantalla con las dimensiones especificadas y la muestra en el centro de la pantalla
    app.resizable(height=False,width=False)
    app.title("Proyecto Programado")

    
    loadMainMenu(secondaryFrame)



#Funcion encargada de crear y mostrar el menu principal
def loadMainMenu(parent:CTk):
    clearScreen(parent)
    btnImage1 = CTkButton(master=parent,text="Select image 1", corner_radius=32,command=selectedimage1)
    btnImage2 = CTkButton(master=parent,text="Select image 2", corner_radius=32,command=selectedimage2)
    btnImage3 = CTkButton(master=parent,text="Select image 3", corner_radius=32,command=selectedimage3)

    btnImage1.place(relx=0.2,rely=0.5,anchor="center")
    btnImage2.place(relx=0.5,rely=0.5,anchor="center")
    btnImage3.place(relx=0.8,rely=0.5,anchor="center")

    createExitBtn()
    
    displayImages(parent)
    
def createExitBtn():
    btnExit = CTkButton(master=app,text="Salir",corner_radius=32,fg_color="red",hover_color="darkred",width=30,command=handleExit)

    btnExit.place(relx=0.95,rely=0.97,anchor="center")

#Funcion encargada de mostrar las imagenes en el menu principal
def displayImages(parent:CTk):
    try:
        image1 = CTkImage(light_image=Image.open(images[0]),size=(200,150))
        imageLabel1 = CTkLabel(parent, image=image1,text="").place(relx=0.2,rely=0.3,anchor="center")

        image2 = CTkImage(light_image=Image.open(images[1]), size=(200,150))
        imageLabel2 = CTkLabel(parent, image=image2,text="").place(relx=0.5,rely=0.3,anchor="center")

        image3 = CTkImage(light_image=Image.open(images[2]),size=(200,150))
        imageLabel3 = CTkLabel(parent, image=image3,text="").place(relx=0.8,rely=0.3,anchor="center")


    except:
        print("An error occured while loading images")

def selectedimage1():
    selectedImageMenu(0,secondaryFrame)

def selectedimage2():
    selectedImageMenu(1,secondaryFrame)
def selectedimage3():
    selectedImageMenu(2,secondaryFrame)

def selectedImageMenu(indexImage:int,parent:CTk):
    clearScreen(parent)
    createReturnBtn(parent)
    
    global image,imageSelectedWidget,imageSelectedLabel
    global angleImage, width, height
    angleImage = 0
    width,height = 300,240
    
    image = Image.open(images[indexImage])

    imageSelectedWidget = CTkImage(light_image=image,size=(300,240))
    imageSelectedLabel = CTkLabel(master=parent,image=imageSelectedWidget,text="")
    imageSelectedLabel.place(relx=0.5,rely=0.3,anchor="center")

    createBTN(parent,"Rotar 10° hacia la izquierda",lambda: rotationHandler(False),0.15,0.6)
    createBTN(parent,"Rotar 10° hacia la derecha",lambda: rotationHandler(True),0.4,0.6)
    
    createBTN(parent,"Agrandar 10 pixeles",lambda: resizingHandler(True),0.65,0.6)
    createBTN(parent,"Encoger 10 pixeles",lambda: resizingHandler(False),0.864,0.6)

    createBTN(parent,"Convertir a escala de grises",grayScaleHandler,0.15,0.7)
    createBTN(parent,"Convertir a blanco y negro",blackAndWhitehandler,0.4,0.7)

    createBTN(parent,"Reiniciar imagen",restoreImage,0.757,0.7,290)

    global slider
    slider = CTkSlider(parent,from_=0.0,to=5.0,command=contrastHandler)
    slider.place(relx=0.5,rely=0.8,anchor="center")
    slider.set(1.0);
    
    labelContrast = CTkLabel(parent, text="Ajustar contraste",fg_color="transparent")
    labelContrast.place(relx=0.2,rely=0.8,anchor="center")

    global labelContrastIndicator
    labelContrastIndicator = CTkLabel(parent, text="Contraste actual: 1.0",fg_color="transparent")
    labelContrastIndicator.place(relx=0.75,rely=0.8,anchor="center")

    createBTN(parent, "Identificar objeto y calcular area",lambda: identifyObjectHandler(parent),0.5,0.9,400)



def rotationHandler(turnRight:bool):
    global angleImage
    angleImage = angleImage + 10 if turnRight else angleImage - 10

    if(angleImage > 360):
        angleImage = 10
    elif(angleImage < 0):
        angleImage = 350
    
    rotated = Transformaciones.RotateImage(image,angleImage)
    imageSelectedWidget.configure(light_image=rotated)
    imageSelectedLabel.configure(image=imageSelectedWidget)

def resizingHandler(increase:bool):
    global width,height

    width = width + 10 if increase else width - 10
    height = height + 10 if increase else height - 10

    resized = Transformaciones.resizeImage(image,width,height)
    imageSelectedWidget.configure(light_image=resized,size=(width,height))
    imageSelectedLabel.configure(image=imageSelectedWidget)

def contrastHandler(value):
    newContrast = Transformaciones.adjustContrast(image,value)
    imageSelectedWidget.configure(light_image=newContrast)
    imageSelectedLabel.configure(image=imageSelectedWidget)
    labelContrastIndicator.configure(text=f"Contraste actual: {round(value,1)}")

def grayScaleHandler():
    grayScaleImage = Transformaciones.grayScale(image)
    imageSelectedWidget.configure(light_image=grayScaleImage)
    imageSelectedLabel.configure(image=imageSelectedWidget)

def blackAndWhitehandler():
    blackWhiteImage = Transformaciones.blackAndWhite(image)
    imageSelectedWidget.configure(light_image=blackWhiteImage)
    imageSelectedLabel.configure(image=imageSelectedWidget)

def restoreImage():
    imageSelectedWidget.configure(light_image=image,size=(300,240))
    imageSelectedLabel.configure(image=imageSelectedWidget)
    
    global angleImage, width, height, slider
    angleImage = 0
    width = 300
    height = 240
    slider.set(1.0)
    contrastHandler(1.0)

def identifyObjectHandler(parent:CTk):
    figure = OD.get_shape_and_area(Transformaciones.blackAndWhite(image))
    topLevel = CTkToplevel(parent)
    topLevel.title("Figura & area")
    topLevel.geometry(f"250x150+{screenWidth}+{screenHeight}")
    topLevel.grab_set()
    topLevel.focus_force()
    label = CTkLabel(topLevel,text=f"Figura: {figure['shape']}    Area: {figure['area_px']}",anchor="center")
    label.pack(pady= 40)
    createBTN(topLevel,"Cerrar",lambda: closeTopLevel(topLevel),0.5,0.7)

def closeTopLevel(topLevel:CTkToplevel):
    topLevel.destroy()

def clearScreen(parent:CTk):
    for widget in parent.winfo_children():
        widget.destroy()

def createReturnBtn(parent:CTk):
    returnBtn = CTkButton(master=parent,text="Regresar",corner_radius=32,fg_color="green",hover_color="darkgreen",width=60,command=handleReturn)
    returnBtn.place(relx=0.85,rely=0.97,anchor="center")

def handleReturn():
    loadMainMenu(secondaryFrame)

def handleExit():
    app.destroy()

def createBTN(parent,text,function,posx,posy,width:int=140):
    btnRotate = CTkButton(master=parent,text=text,command=function,width=width)
    btnRotate.place(relx=posx,rely=posy,anchor="center")

if __name__ == "__main__":
    createWindow(app,700,600)
    app.mainloop()
