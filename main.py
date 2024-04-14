import tkinter as tk
from tkinter import filedialog, messagebox
import nibabel as nib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class NiiViewerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Segmentaciones")
        self.frame = tk.Frame(self.master)
        self.frame.pack()
        # self.file_path = filedialog.askopenfilename(filetypes=[("NIfTI files", "*.nii"), ("All files", "*.*")])
        # print(self.file_path)
        self.file_path = "file.nii"
        self.img = nib.load(self.file_path)
        self.img_data = self.img.get_fdata() 
        self.update_delay = 100 
        self.update_slice_id = None
        self.z_slider = tk.Scale(self.frame, from_=0, to=1, orient=tk.HORIZONTAL, resolution=1, command=self.update_slice)
        self.z_slider.pack()
        self.z_slider.config(to=self.img_data.shape[2] - 1)
        self.z_slider.set(self.img_data.shape[2] // 2)
        self.z_slider.bind("<MouseWheel>", self.desplazamiento)
        self.canvas = None
        self.cid_press1 = None
        self.segment_button = tk.Button(self.frame, text="Segmentación", command=self.options)
        self.segment_button.pack()
        self.segmented_img = None
        self.segmented_z_slider = None
        self.segmented_canvas = None
        self.trazos = []  # Lista para almacenar los trazos
        self.trazos_guardados = False  # Indica si se cargaron trazos desde un archivo

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
            # Bind event handlers for drawing
            self.canvas.mpl_connect('button_press_event', self.on_press)
            self.canvas.mpl_connect('motion_notify_event', self.on_motion)
            # Dibujar trazos guardados si están disponibles
            if self.trazos_guardados:
                self.dibujar_trazos()

    def on_press(self, event):
        self.x_prev = event.xdata
        self.y_prev = event.ydata

    def on_motion(self, event):
        if event.button == 1:  # Solo dibujar si el clic izquierdo está presionado
            if self.x_prev is None or self.y_prev is None:
                return
            x, y = int(event.xdata), int(event.ydata)
            plt.gca().plot([self.x_prev, x], [self.y_prev, y], color='red', linewidth=2)
            self.x_prev = x
            self.y_prev = y
            self.trazos.append(((self.x_prev, self.y_prev), (x, y)))  # Almacenar trazo
            self.canvas.draw()

    def desplazamiento(self, event):
        if event.delta > 0:
            self.z_slider.set(self.z_slider.get() + 1)
        else:
            self.z_slider.set(self.z_slider.get() - 1)

    def options(self):
        dialog = tk.Toplevel(self.master)
        dialog.title("Opciones de Segmentación")
        frame = tk.Frame(dialog)
        frame.pack()
        def destU():
            dialog.destroy()
            self.umbral()
        def destI():
            dialog.destroy()
            self.isodata()
        def destC():
            dialog.destroy()
            self.crecimiento_regiones()
        def destK():
            dialog.destroy()
            self.kmeans()
        threshold_button = tk.Button(frame, text="Umbral", command=destU, width=15, height=2)
        threshold_button.pack(side=tk.LEFT, padx=5, pady=10)
        isodata_button = tk.Button(frame, text="Isodata", command=destI, width=15, height=2)
        isodata_button.pack(side=tk.LEFT, padx=5, pady=10)
        region_growing_button = tk.Button(frame, text="Crecimiento de Regiones", command=destC, width=20, height=2)
        region_growing_button.pack(side=tk.LEFT, padx=5, pady=10)
        kmeans_button = tk.Button(frame, text="K-Means", command=destK, width=15, height=2)
        kmeans_button.pack(side=tk.LEFT, padx=5, pady=10)
    def isodata(self, initial_threshold=0, tolerance=1):
        threshold = initial_threshold
        while True:
            segmented_image = self.threshold_imagen(self.img_data, threshold)
            foreground_mean = np.mean(self.img_data[segmented_image == 1])
            background_mean = np.mean(self.img_data[segmented_image == 0])
            new_threshold = (foreground_mean + background_mean) / 2
            if abs(new_threshold - threshold) < tolerance:
                break
            threshold = new_threshold

        self.segmented_volume = self.threshold_imagen(self.img_data, threshold)

        self.isodata_window = tk.Toplevel(self.master)
        # self.isodata_window.title("Segmentación Isodata")
        self.z_slice_var = tk.IntVar()
        self.z_slice_var.set(self.img_data.shape[2] // 2)
        self.z_slice_slider = tk.Scale(self.isodata_window, from_=0, to=self.img_data.shape[2] - 1, orient=tk.HORIZONTAL, variable=self.z_slice_var, command=self.update_segmented_slice)
        self.z_slice_slider.pack()
        # Update the segmented slice after convergence
        self.update_segmented_slice()

        save_button = tk.Button(self.isodata_window, text="Guardar como NIfTI", command=self.guardar_segmentacion_nifti)
        save_button.pack(pady=10)

    def update_segmented_slice(self, event=None):
        if hasattr(self, 'canvas'):
            self.canvas.get_tk_widget().destroy()

        z_slice = self.z_slice_var.get()
        fig, ax = plt.subplots()
        ax.imshow(self.segmented_volume[:, :, z_slice], cmap='gray')
        ax.set_title("Segmentación Isodata - Slice {}".format(z_slice))
        ax.axis('off')
        self.canvas = FigureCanvasTkAgg(fig, master=self.isodata_window)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack()


    def threshold_imagen(self, image, threshold):
        return (image > threshold).astype(np.uint8)

    def crecimiento_regiones(self):
        if not self.trazos:
            messagebox.showerror("Error", "No hay trazos disponibles para el crecimiento de regiones.")
            return

        labels = np.zeros_like(self.img_data[:, :, self.z_slice])
        intensity_threshold = 100

        for trazo in self.trazos:
            seed_x, seed_y = trazo[0]
            seed_value = self.img_data[seed_y, seed_x, self.z_slice]

            queue = [trazo[0]]

            while queue:
                x, y = queue.pop(0)
                labels[y, x] = 1

                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if 0 <= x + dx < self.img_data.shape[1] and 0 <= y + dy < self.img_data.shape[0]:
                            if labels[y + dy, x + dx] == 0 and abs(self.img_data[y + dy, x + dx, self.z_slice] - seed_value) < intensity_threshold:
                                queue.append((x + dx, y + dy))
                                labels[y + dy, x + dx] = 1

        self.growing_dialog = tk.Toplevel(self.master)
        self.growing_dialog.title("Segmentación por Crecimiento de Regiones")
        self.canvas2 = tk.Canvas(self.growing_dialog)
        self.fig2, self.ax2 = plt.subplots()
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.growing_dialog)
        self.canvas2.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.ax2.imshow(labels, cmap="gray")
        self.ax2.axis("off")
        self.canvas2.draw_idle()

        save_button = tk.Button(self.growing_dialog, text="Guardar como PNG", command=lambda: self.guardar_crecimiento(labels), width=15, height=2)
        save_button.pack(side=tk.BOTTOM)

    def guardar_crecimiento(self, data):
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if file_path:
            plt.imsave(file_path, data, cmap='gray')

    def kmeans(self, num_clusters=2, max_iterations=100):
        flattened_img = self.img_data.flatten()
        centroids = np.random.choice(flattened_img, size=num_clusters)
        for _ in range(max_iterations):
            distances = np.abs(flattened_img[:, None] - centroids)
            labels = np.argmin(distances, axis=1)
            new_centroids = []
            for i in range(num_clusters):
                cluster_points = flattened_img[labels == i]
                if len(cluster_points) > 0:
                    new_centroids.append(np.mean(cluster_points))
                else:
                    new_centroids.append(centroids[i])
            new_centroids = np.array(new_centroids)
            if np.all(centroids == new_centroids):
                break
            centroids = new_centroids
        self.segmented_img = centroids[labels].reshape(self.img_data.shape)
        self.show_segmentation()

    def show_segmentation(self):
        if self.segmented_canvas:
            self.segmented_canvas.get_tk_widget().destroy()

        fig, ax = plt.subplots()
        ax.imshow(self.segmented_img[:, :, self.z_slider.get()], cmap='gray')
        ax.set_title("Segmentación K-Means")
        ax.axis('off')

        window = tk.Toplevel(self.master)
        window.title("Visualización de Segmentación")

        self.segmented_canvas = FigureCanvasTkAgg(fig, master=window)
        self.segmented_canvas.draw()
        self.segmented_canvas.get_tk_widget().pack(fill="both", expand=True)

        self.segmented_z_slider = tk.Scale(window, from_=0, to=self.img_data.shape[2] - 1, orient=tk.HORIZONTAL, resolution=1, command=self.update_segmented_slice)
        self.segmented_z_slider.pack(fill="x")
        self.segmented_z_slider.set(self.z_slider.get())

        save_button = tk.Button(window, text="Guardar como NIfTI", command=self.guardar_segmentacion_nifti)
        save_button.pack(pady=10)

    def update_segmented_slice(self, event=None):
        if self.segmented_img is not None:
            self.z_slice = self.segmented_z_slider.get()
            plt.clf()
            plt.imshow(self.segmented_img[:, :, self.z_slice], cmap='gray')
            plt.title("Corte en Z = {}".format(self.z_slice))
            plt.axis('off')
            plt.tight_layout()
            self.segmented_canvas.draw()

    def guardar_segmentacion_nifti(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".nii", filetypes=[("NIfTI files", "*.nii")])
        if file_path:
            segmented_img_nii = nib.Nifti1Image(self.segmented_img, self.img.affine)
            nib.save(segmented_img_nii, file_path)

    def guardar_trazos(self, file_path):
        with open(file_path, 'w') as f:
            for trazo in self.trazos:
                f.write(f"{trazo[0][0]} {trazo[0][1]} {trazo[1][0]} {trazo[1][1]}\n")

    def cargar_trazos(self, file_path):
        with open(file_path, 'r') as f:
            for line in f:
                x1, y1, x2, y2 = map(float, line.split())
                self.trazos.append(((x1, y1), (x2, y2)))
        self.trazos_guardados = True

    def dibujar_trazos(self):
        if self.trazos_guardados:
            for trazo in self.trazos:
                plt.gca().plot([trazo[0][0], trazo[1][0]], [trazo[0][1], trazo[1][1]], color='red', linewidth=2)
            self.canvas.draw()

    

def main():
    root = tk.Tk()
    app = NiiViewerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
