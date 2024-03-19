import tkinter as tk
from tkinter import filedialog,messagebox
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
        self.cid_press1 = None

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
            self.cid_press1 = self.canvas.mpl_connect('button_press_event', self.on_click_region_growing)
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
        # Calcular el histograma de la imagen
        histogram, bins = np.histogram(self.img_data[:, :, self.z_slice].ravel(), bins=256, range=(0, 256))

        # Inicializar los centroides utilizando K-Means
        kmeans = KMeans(n_clusters=2, random_state=0).fit(histogram.reshape(-1, 1))
        centroids = kmeans.cluster_centers_.ravel()

        # Definir los límites iniciales de los grupos
        low_threshold, high_threshold = centroids

        # Iterar hasta que los centroides converjan
        while True:
            # Calcular el nuevo umbral como el promedio de los centroides
            new_threshold = (low_threshold + high_threshold) / 2

            # Asignar cada píxel al grupo correspondiente
            group_1 = self.img_data[:, :, self.z_slice] <= new_threshold
            group_2 = self.img_data[:, :, self.z_slice] > new_threshold

            # Calcular los nuevos centroides
            new_centroid_1 = np.mean(self.img_data[:, :, self.z_slice][group_1])
            new_centroid_2 = np.mean(self.img_data[:, :, self.z_slice][group_2])

            # Verificar si los centroides convergen
            if abs(new_centroid_1 - centroids[0]) < 1e-5 and abs(new_centroid_2 - centroids[1]) < 1e-5:
                break

            # Actualizar los centroides y los umbrales
            centroids = [new_centroid_1, new_centroid_2]
            low_threshold, high_threshold = min(centroids), max(centroids)

        # Segmentar la imagen utilizando los umbrales finales
        segmented_img = np.zeros_like(self.img_data[:, :, self.z_slice])
        segmented_img[self.img_data[:, :, self.z_slice] <= new_threshold] = 0
        segmented_img[self.img_data[:, :, self.z_slice] > new_threshold] = 1

        # Mostrar la imagen segmentada y su histograma
        fig, axes = plt.subplots(1, 2, figsize=(10, 5))
        axes[0].imshow(segmented_img, cmap='gray')
        axes[0].set_title("Segmentación de Isodata")
        axes[0].axis('off')
        axes[1].bar(bins[:-1], histogram, width=1)
        axes[1].set_title("Histograma")
        axes[1].set_xlabel("Intensidad de píxel")
        axes[1].set_ylabel("Frecuencia")
        plt.show()

    def region_growth_segmentation(self):
        messagebox.showinfo("Segmentación", "Método de Segmentación: Crecimiento de Regiones")
        messagebox.showinfo("Segmentación", "Seleccione una semilla haciendo clic en la imagen.")

        # Desconectar cualquier conexión de clic anterior
        self.canvas.mpl_disconnect(self.cid_press1)
        self.cid_press1 = self.canvas.mpl_connect('button_press_event', self.on_click_region_growing)

    def on_click_region_growing(self, event):
        x, y = int(event.xdata), int(event.ydata)
        self.seed_point = (x, y)
        self.region_growing_segmentation()

    def region_growing_segmentation(self):
        if not hasattr(self, 'seed_point'):
            messagebox.showerror("Error", "Primero seleccione una semilla haciendo clic en la imagen.")
            return

        seed_x, seed_y = self.seed_point
        seed_value = self.img_data[seed_y, seed_x, self.z_slice]  # Obtener el valor de intensidad de la semilla

        # Inicializar la matriz de etiquetas para marcar los píxeles visitados
        labels = np.zeros_like(self.img_data[:, :, self.z_slice])

        # Inicializar una lista de píxeles por visitar
        queue = [(seed_x, seed_y)]

        # Definir la tolerancia de intensidad para el crecimiento de regiones
        intensity_threshold = 100  # Puedes ajustar este valor según tus necesidades

        # Mientras haya píxeles por visitar en la cola
        while queue:
            x, y = queue.pop(0)
            # Marcar el píxel como visitado
            labels[y, x] = 1

            # Comprobar los píxeles adyacentes
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    # Verificar si el píxel está dentro de la imagen
                    if 0 <= x + dx < self.img_data.shape[1] and 0 <= y + dy < self.img_data.shape[0]:
                        # Verificar si el píxel no ha sido visitado y si cumple el criterio de similitud
                        if labels[y + dy, x + dx] == 0 and abs(self.img_data[y + dy, x + dx, self.z_slice] - seed_value) < intensity_threshold:
                            # Agregar el píxel a la cola para visitar en el próximo paso
                            queue.append((x + dx, y + dy))
                            # Marcar el píxel como parte de la región segmentada
                            labels[y + dy, x + dx] = 1

        # Visualizar la región segmentada
        self.threshold_dialog = tk.Toplevel(self.master)  # Crear el diálogo de segmentación si no existe
        self.threshold_dialog.title("Segmentación por Crecimiento de Regiones")

        self.canvas2 = tk.Canvas(self.threshold_dialog)
        self.fig2, self.ax2 = plt.subplots()
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.threshold_dialog)
        self.canvas2.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.ax2.imshow(labels, cmap="gray")  # Utilizar 'labels' para mostrar la segmentación
        self.ax2.axis("off")
        self.canvas2.draw_idle()

def main():
    root = tk.Tk()
    app = NiiViewerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
