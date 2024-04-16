import tkinter as tk
import segmentacion as segment
import procesamiento as process

def segmentacion():
    # Aquí puedes colocar el código para la funcionalidad de segmentación
    segment.main()
    print("Segmentación")

def procesamiento():
    # Aquí puedes colocar el código para la funcionalidad de procesamiento
    process.main()
    print("Procesamiento")

# Crear la ventana principal
ventana = tk.Tk()
ventana.title("Aplicación")

# Crear un contenedor para los botones
contenedor_botones = tk.Frame(ventana)
contenedor_botones.pack(padx=10, pady=10)
# Colores
color_boton = "#8B4513"  # cafe
color_texto = "white"
# Crear los botones dentro del contenedor
btn_segmentacion = tk.Button(contenedor_botones, text="Segmentación", command=segmentacion,width=30, height=20, bg=color_boton, fg=color_texto)
btn_segmentacion.pack(side=tk.LEFT, padx=5)

btn_procesamiento = tk.Button(contenedor_botones, text="Procesamiento", command=procesamiento,width=30, height=20, bg=color_boton, fg=color_texto)
btn_procesamiento.pack(side=tk.LEFT, padx=5)

# Ejecutar el bucle de eventos
ventana.mainloop()
