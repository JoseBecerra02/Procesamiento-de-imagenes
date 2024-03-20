import tkinter as tk
from tkinter import filedialog, messagebox
import nibabel as nib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from skimage.filters import threshold_otsu

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
            self.z_slice = self.z_slider.get()
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
        def destU():
            dialog.destroy()
            self.threshold_segmentation()
        def destI():
            dialog.destroy()
            self.isodata_segmentation()
        def destC():
            dialog.destroy()
            num_seeds_dialog = tk.Toplevel(self.master)
            num_seeds_dialog.title("Número de Semillas")
            tk.Label(num_seeds_dialog, text="Ingrese el número de semillas que desea seleccionar:").pack()
            num_seeds_entry = tk.Entry(num_seeds_dialog)
            num_seeds_entry.pack()
            tk.Button(num_seeds_dialog, text="Aceptar", command=lambda: self.region_growth_segmentation(int(num_seeds_entry.get()))).pack()
        def destK():
            dialog.destroy()
            self.kmeans_segmentation()
        threshold_button = tk.Button(frame, text="Umbral", command=destU, width=15, height=2)
        threshold_button.pack(side=tk.LEFT, padx=5, pady=10)
        isodata_button = tk.Button(frame, text="Isodata", command=destI, width=15, height=2)
        isodata_button.pack(side=tk.LEFT, padx=5, pady=10)
        region_growing_button = tk.Button(frame, text="Crecimiento de Regiones", command=destC, width=20, height=2)
        region_growing_button.pack(side=tk.LEFT, padx=5, pady=10)
        kmeans_button = tk.Button(frame, text="K-Means", command=destK, width=15, height=2)
        kmeans_button.pack(side=tk.LEFT, padx=5, pady=10)

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
        # Visualizar la imagen segmentada inicialmente
        update_segmentation(threshold_value)
        
        # Agregar el botón de guardar
        save_button = tk.Button(frame, text="Guardar Segmentación", command=lambda: self.save_segmentation(segmented_img))
        save_button.pack(side=tk.BOTTOM, padx=5, pady=10)

    def save_segmentation(self, segmented_img):
        if segmented_img is not None:
            file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
            if file_path:
                plt.imsave(file_path, segmented_img, cmap='gray')
    
    def isodata_segmentation(self):
        # Obtener la imagen actual en la vista
        current_slice = self.img_data[:, :, self.z_slice]

        # Convertir la imagen en un vector unidimensional
        flat_data = current_slice.flatten()

        # Definir los límites inicial y final para el valor umbral
        min_threshold = np.min(flat_data)
        max_threshold = np.max(flat_data)

        # Inicializar el valor umbral como el promedio de los límites inicial y final
        threshold = (min_threshold + max_threshold) / 2

        # Definir el número máximo de iteraciones
        max_iterations = 50
        iterations = 0

        while True:
            # Segmentar la imagen utilizando el valor umbral actual
            segmented_img = np.zeros_like(current_slice)
            segmented_img[current_slice >= threshold] = 255

            # Calcular los promedios de intensidad para cada clase
            class1_mean = np.mean(flat_data[segmented_img.flatten() == 0])
            class2_mean = np.mean(flat_data[segmented_img.flatten() == 255])

            # Calcular el nuevo valor umbral como el promedio de los promedios de intensidad
            new_threshold = (class1_mean + class2_mean) / 2

            # Si el valor umbral no cambia o se alcanza el número máximo de iteraciones, detener el bucle
            if abs(threshold - new_threshold) < 0.5 or iterations >= max_iterations:
                break

            threshold = new_threshold
            iterations += 1

        # Mostrar la imagen segmentada en una nueva ventana
        fig, ax = plt.subplots()
        ax.imshow(segmented_img, cmap='gray')
        ax.set_title("Segmentación ISODATA")
        ax.axis('off')

        # Crear una ventana de Tkinter y mostrar la figura en ella
        window = tk.Toplevel(self.master)
        window.title("Segmentación ISODATA")
        canvas = FigureCanvasTkAgg(fig, master=window)
        canvas.draw()
        canvas.get_tk_widget().pack()

        # Agregar un botón para guardar la imagen segmentada
        save_button = tk.Button(window, text="Guardar como PNG", command=lambda: self.save_segmentation(segmented_img))
        save_button.pack(pady=10)

    def save_segmentation(self, segmented_img):
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if file_path:
            plt.imsave(file_path, segmented_img, cmap='gray')
            messagebox.showinfo("Guardado", "La segmentación se ha guardado exitosamente como PNG.")

    def region_growth_segmentation(self, num_seeds):
        # messagebox.showinfo("Segmentación", f"Seleccione {num_seeds} semillas haciendo clic en la imagen.")

        # Desconectar cualquier conexión de clic anterior
        if self.canvas:
            self.canvas.mpl_disconnect(self.cid_press1)
        self.cid_press1 = self.canvas.mpl_connect('button_press_event', lambda event: self.on_click_region_growing(event, num_seeds))


    def on_click_region_growing(self, event, num_seeds):
        if not hasattr(self, 'seed_points'):
            self.seed_points = []
        x, y = int(event.xdata), int(event.ydata)
        self.seed_points.append((x, y))
        if len(self.seed_points) == num_seeds:
            self.region_growing_segmentation(num_seeds)


    def region_growing_segmentation(self, num_seeds):
        if not hasattr(self, 'seed_points') or len(self.seed_points) != num_seeds:
            messagebox.showerror("Error", f"Debe seleccionar exactamente {num_seeds} semillas haciendo clic en la imagen.")
            return

        labels = np.zeros_like(self.img_data[:, :, self.z_slice])

        intensity_threshold = 100

        for seed_point in self.seed_points:
            seed_x, seed_y = seed_point
            seed_value = self.img_data[seed_y, seed_x, self.z_slice]

            queue = [seed_point]

            while queue:
                x, y = queue.pop(0)
                labels[y, x] = 1

                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if 0 <= x + dx < self.img_data.shape[1] and 0 <= y + dy < self.img_data.shape[0]:
                            if labels[y + dy, x + dx] == 0 and abs(self.img_data[y + dy, x + dx, self.z_slice] - seed_value) < intensity_threshold:
                                queue.append((x + dx, y + dy))
                                labels[y + dy, x + dx] = 1

        self.threshold_dialog = tk.Toplevel(self.master)
        self.threshold_dialog.title("Segmentación por Crecimiento de Regiones")

        self.canvas2 = tk.Canvas(self.threshold_dialog)
        self.fig2, self.ax2 = plt.subplots()
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.threshold_dialog)
        self.canvas2.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.ax2.imshow(labels, cmap="gray")
        self.ax2.axis("off")
        self.canvas2.draw_idle()

        # Añadir botón de guardado
        save_button = tk.Button(self.threshold_dialog, text="Guardar como PNG", command=lambda: self.save_as_png(labels, "Segmentacion_region_growing.png"), width=15, height=2)
        save_button.pack(side=tk.BOTTOM)

    def save_as_png(self, data, filename):
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if file_path:
            plt.imsave(file_path, data, cmap='gray')

    def kmeans_segmentation(self, num_clusters=2, max_iterations=100):
        # Obtener la imagen 2D en la posición z actual
        img_slice = self.img_data[:, :, self.z_slice]
        # Convertir la imagen 2D en un arreglo unidimensional
        flattened_img = img_slice.flatten()
        # Inicializar centroides aleatorios
        centroids = np.random.choice(flattened_img, size=num_clusters)
        for _ in range(max_iterations):
            # Calcular la distancia euclidiana entre cada píxel y los centroides
            distances = np.abs(flattened_img[:, None] - centroids)
            # Asignar cada píxel al clúster con la distancia mínima
            labels = np.argmin(distances, axis=1)
            # Actualizar los centroides como el promedio de los píxeles en cada clúster
            new_centroids = []
            for i in range(num_clusters):
                cluster_points = flattened_img[labels == i]
                if len(cluster_points) > 0:
                    new_centroids.append(np.mean(cluster_points))
                else:
                    # Si un clúster está vacío, mantener el centroide anterior
                    new_centroids.append(centroids[i])
            new_centroids = np.array(new_centroids)
            # Si los centroides no cambian mucho, salir del bucle
            if np.all(centroids == new_centroids):
                break
            centroids = new_centroids
        # Reconstruir la imagen segmentada usando los centroides finales
        segmented_img = centroids[labels].reshape(img_slice.shape)
        # Visualizar la imagen segmentada
        plt.figure()
        plt.imshow(segmented_img, cmap='gray')
        plt.title("Segmentación K-Means")
        plt.axis('off')
        plt.show()

def main():
    root = tk.Tk()
    app = NiiViewerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()