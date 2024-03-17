import tkinter as tk
from tkinter import filedialog
import nibabel as nib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from skimage.filters import threshold_otsu
from sklearn.cluster import KMeans
import os

class NiiViewerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Segmentaciones")
        
        self.frame = tk.Frame(self.master)
        self.frame.pack()

        # self.file_path = filedialog.askopenfilename(filetypes=[("NIfTI files", "*.nii"), ("All files", "*.*")])
        self.file_path = "file.nii"
        self.img = nib.load(self.file_path)
        self.img_data = self.img.get_fdata()    

        self.original_folder = os.path.dirname(self.file_path)    

        self.update_delay = 100  # Milisegundos
        self.update_slice_id = None

        self.z_slider = tk.Scale(self.frame, from_=0, to=1, orient=tk.HORIZONTAL, resolution=1, command=self.update_slice)
        self.z_slider.pack()
        self.z_slider.config(to=self.img_data.shape[2] - 1)
        self.z_slider.set(self.img_data.shape[2] // 2)

        self.z_slider.bind("<MouseWheel>", self.mouse_wheel)

        self.canvas = None


        self.segment_button = tk.Button(self.frame, text="Segmentación", command=self.segmentation_options)
        self.segment_button.pack()

    def update_slice(self, event=None):
        if self.update_slice_id:
            self.master.after_cancel(self.update_slice_id)
        self.update_slice_id = self.master.after(self.update_delay, self._update_slice)

    def _update_slice(self):
        if self.img_data is not None:
            self.z_slice = int(self.z_slider.get())
            plt.clf()
            plt.imshow(self.img_data[:, :, self.z_slice], cmap='gray')
            plt.title("Corte en Z = {}".format(self.z_slice))
            plt.axis('off')
            plt.tight_layout()

            if self.canvas:
                self.canvas.get_tk_widget().destroy()

            self.canvas = FigureCanvasTkAgg(plt.gcf(), master=self.frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack()



    def mouse_wheel(self, event):
        if event.delta > 0:
            self.z_slider.set(self.z_slider.get() + 1)
        else:
            self.z_slider.set(self.z_slider.get() - 1)

    def segmentation_options(self):
        dialog = tk.Toplevel(self.master)
        dialog.title("Opciones de Segmentación")

        frame = tk.Frame(dialog)
        frame.pack()
        def destU ():
            dialog.destroy()
            self.threshold_segmentation()
        def destI ():
            dialog.destroy()
            self.isodata_segmentation()
        def destC ():
            dialog.destroy()
            self.region_growth_segmentation()
        def destK ():
            dialog.destroy()
            self.kmeans_segmentation()
            

        threshold_button = tk.Button(frame, text="Umbral", command=destU, width=15, height=2)
        threshold_button.pack(side=tk.LEFT, padx=5,pady= 10)

        isodata_button = tk.Button(frame, text="Isodata", command=destI, width=15, height=2)
        isodata_button.pack(side=tk.LEFT, padx=5,pady= 10)

        region_growing_button = tk.Button(frame, text="Crecimiento de Regiones", command=destC, width=20, height=2)
        region_growing_button.pack(side=tk.LEFT, padx=5,pady= 10)

        kmeans_button = tk.Button(frame, text="K-Means", command=destK, width=15, height=2)
        kmeans_button.pack(side=tk.LEFT, padx=5,pady= 10)


    def threshold_segmentation(self):
        # min_pixel_value = np.min(self.img_data[:, :, self.z_slice])
        max_pixel_value = np.max(self.img_data[:, :, self.z_slice])
        
        # Calcular el umbral inicial usando el método de Otsu
        threshold_value = threshold_otsu(self.img_data[:, :, self.z_slice])
        # Crear una nueva ventana para la segmentación
        threshold_window = tk.Toplevel(self.master)
        threshold_window.title("Segmentación por Umbralización")

        # Crear un marco para contener el título y el control deslizante
        frame = tk.Frame(threshold_window)
        frame.pack()

        # Crear el título para mostrar el valor del umbral
        threshold_label = tk.Label(frame, text="Segmentación con umbral {}".format(threshold_value), font=("Helvetica", 14))
        threshold_label.pack(side=tk.TOP)

        # Función para actualizar la segmentación según el valor del slider
        def update_segmentation(value):
            threshold_value = int(value)
            segmented_img = self.img_data[:, :, self.z_slice] > threshold_value
            im.set_data(segmented_img)  # Actualizar solo los datos de la imagen
            threshold_label.config(text="Segmentación con umbral {}".format(threshold_value))
            fig.canvas.draw()

        # Crear un subplot para mostrar la imagen segmentada
        fig, ax = plt.subplots()
        ax.axis('off')
        fig.tight_layout()
        fig_canvas = FigureCanvasTkAgg(fig, master=frame)
        fig_canvas.draw()
        fig_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # Plotear la imagen segmentada inicialmente
        segmented_img = self.img_data[:, :, self.z_slice] > threshold_value
        im = ax.imshow(segmented_img, cmap='gray')
        # Slider para ajustar el umbral
        self.threshold_slider = tk.Scale(frame, from_=0, to=max_pixel_value, orient=tk.HORIZONTAL, length=200, command=update_segmentation)
        self.threshold_slider.set(threshold_value)
        self.threshold_slider.pack(side=tk.TOP)

        save_button = tk.Button(frame, text="Guardar como PNG", command=lambda: self.save_as_png(segmented_img), width=15, height=2)
        save_button.pack(side=tk.BOTTOM)

        # Visualizar la imagen segmentada inicialmente
        update_segmentation(threshold_value)
    def save_as_png(self, segmented_img):
        
        # Construir la ruta completa del archivo PNG usando la ruta de la carpeta original y el nombre del archivo original
        png_file_path = os.path.join(self.original_folder, "Segmentacion_umbral.png")
        
        # Guardar la imagen segmentada como un archivo PNG
        plt.imsave(png_file_path, segmented_img, cmap='gray')
        print("Imagen guardada como:", png_file_path)

        

    def isodata_segmentation(self):
        pass  # Implementa la segmentación de Isodata

    def region_growth_segmentation(self):
        pass  # Implementa la segmentación de crecimiento de regiones

    def kmeans_segmentation(self):
        pass  # Implementa la segmentación de kmeans

def main():
    root = tk.Tk()
    app = NiiViewerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
