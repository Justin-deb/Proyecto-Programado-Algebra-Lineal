from customtkinter import *
from PIL import Image

app = CTk()
app.geometry("800x700")
app.resizable(height=False,width=False)

#Funcion encargada de crear y mostrar el menu principal
def loadMainMenu():
    btnImage1 = CTkButton(master=app,text="Select image 1", corner_radius=32)
    btnImage2 = CTkButton(master=app,text="Select image 2", corner_radius=32)
    btnImage3 = CTkButton(master=app,text="Select image 3", corner_radius=32)

    btnImage1.place(relx=0.2,rely=0.5,anchor="center")
    btnImage2.place(relx=0.5,rely=0.5,anchor="center")
    btnImage3.place(relx=0.8,rely=0.5,anchor="center")
    
    displayImages()
    

def loadImages():
    try:
        listImages = ["./Resources/Image1.png","./Resources/Image2.png","./Resources/Image3.png"]
        return listImages
    except:
        print("Images not founded")
    
def displayImages():
    try:
        images = loadImages()
        
        image1 = CTkImage(light_image=Image.open(images[0]),size=(200,150))
        imageLabel1 = CTkLabel(app, image=image1,text="Image1").place(relx=0.2,rely=0.3,anchor="center")

        image2 = CTkImage(light_image=Image.open(images[1]), size=(200,150))
        imageLabel2 = CTkLabel(app, image=image2,text="Image2").place(relx=0.5,rely=0.3,anchor="center")

        image3 = CTkImage(light_image=Image.open(images[2]),size=(200,150))
        imageLabel3 = CTkLabel(app, image=image3,text="Image3").place(relx=0.8,rely=0.3,anchor="center")


    except:
        print("An error occured while loading images")



if __name__ == "__main__":
    loadMainMenu()
    app.mainloop()



