from customtkinter import *
from PIL import Image

#Funcion encargada de cargar las imagenes de la computadora en una lista
def loadImages():
    try:
        listImages = ["./Resources/Image1.png","./Resources/Image2.png","./Resources/Image3.png"]
        return listImages
    except:
        print("Images not founded")

#crea la instancia de Custom Tkinter(GUI)
app = CTk()

images = loadImages()

secondaryFrame = CTkFrame(master=app,fg_color="transparent")
secondaryFrame.pack(expand=True,fill="both")

#Funcion se encarga de crear la pantalla, configurarla y centrarla
def createWindow(parent:CTk, width, height):
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
        imageLabel1 = CTkLabel(parent, image=image1,text="Image1").place(relx=0.2,rely=0.3,anchor="center")

        image2 = CTkImage(light_image=Image.open(images[1]), size=(200,150))
        imageLabel2 = CTkLabel(parent, image=image2,text="Image2").place(relx=0.5,rely=0.3,anchor="center")

        image3 = CTkImage(light_image=Image.open(images[2]),size=(200,150))
        imageLabel3 = CTkLabel(parent, image=image3,text="Image3").place(relx=0.8,rely=0.3,anchor="center")


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
    imageSelected = CTkImage(light_image=Image.open(images[indexImage]),size=(300,240))
    imageSelectedLabel = CTkLabel(master=parent,image=imageSelected,text="Image selected").place(relx=0.5,rely=0.3,anchor="center")

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

if __name__ == "__main__":
    createWindow(app,700,600)
    app.mainloop()



