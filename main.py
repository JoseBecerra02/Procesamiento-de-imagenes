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
            num_seeds_dialog = tk.Toplevel(self.master)
            num_seeds_dialog.title("Número de Semillas")
            tk.Label(num_seeds_dialog, text="Ingrese el número de semillas que desea seleccionar:").pack()
            num_seeds_entry = tk.Entry(num_seeds_dialog)
            num_seeds_entry.pack()
            def start_segmentation():
                num_seeds = int(num_seeds_entry.get())
                num_seeds_dialog.destroy()
                self.crecimiento_regiones(num_seeds)
            tk.Button(num_seeds_dialog, text="Aceptar", command=start_segmentation).pack()
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

    def umbral(self):
        # min_pixel_value = np.min(self.img_data[:, :, self.z_slice])
        max_pixel_value = np.max(self.img_data[:, :, self.z_slice])
        threshold_value = 0
        threshold_window = tk.Toplevel(self.master)
        threshold_window.title("Segmentación por Umbralización")
        frame = tk.Frame(threshold_window)
        frame.pack()
        threshold_label = tk.Label(frame, text="Segmentación con umbral {}".format(threshold_value), font=("Helvetica", 14))
        threshold_label.pack(side=tk.TOP)
        def update_umbral(value):
            threshold_value = int(value)
            segmented_img = self.img_data[:, :, self.z_slice] > threshold_value
            im.set_data(segmented_img) 
            threshold_label.config(text="Segmentación con umbral {}".format(threshold_value))
            fig.canvas.draw()
        fig, ax = plt.subplots()
        ax.axis('off')
        fig.tight_layout()
        fig_canvas = FigureCanvasTkAgg(fig, master=frame)
        fig_canvas.draw()
        fig_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        segmented_img = self.img_data[:, :, self.z_slice] > threshold_value
        im = ax.imshow(segmented_img, cmap='gray')
        self.threshold_slider = tk.Scale(frame, from_=0, to=max_pixel_value, orient=tk.HORIZONTAL, length=200, command=update_umbral)
        self.threshold_slider.set(threshold_value)
        self.threshold_slider.pack(side=tk.TOP)
        update_umbral(threshold_value)
        
        save_button = tk.Button(frame, text="Guardar Segmentación", command=lambda: self.guardar_umbral(segmented_img))
        save_button.pack(side=tk.BOTTOM, padx=5, pady=10)

    def guardar_umbral(self, segmented_img):
        if segmented_img is not None:
            file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
            if file_path:
                plt.imsave(file_path, segmented_img, cmap='gray')
    
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

        segmented_image = self.threshold_imagen(self.img_data, threshold)
        isodata_window = tk.Toplevel(self.master)
        isodata_window.title("Segmentación Isodata")
        fig, ax = plt.subplots()
        ax.imshow(segmented_image[:, :, self.z_slider.get()], cmap='gray')
        ax.set_title("Segmentación Isodata")
        ax.axis('off')
        canvas = FigureCanvasTkAgg(fig, master=isodata_window)
        canvas.draw()
        canvas.get_tk_widget().pack()


    def threshold_imagen(self, image, threshold):
        return (image > threshold).astype(np.uint8)


    def crecimiento_regiones(self, num_seeds):
        messagebox.showinfo("Segmentación", f"Seleccione {num_seeds} semillas haciendo clic en la imagen.")

        if self.canvas:
            self.canvas.mpl_disconnect(self.cid_press1)
        self.cid_press1 = self.canvas.mpl_connect('button_press_event', lambda event: self.seleccion_semilas(event, num_seeds))


    def seleccion_semilas(self, event, num_seeds):
        if not hasattr(self, 'seed_points'):
            self.seed_points = []
        x, y = int(event.xdata), int(event.ydata)
        self.seed_points.append((x, y))
        if len(self.seed_points) == num_seeds:
            self.seg_crecimiento()


    def seg_crecimiento(self):
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
        img_slice = self.img_data[:, :, self.z_slice]
        flattened_img = img_slice.flatten()
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
        segmented_img = centroids[labels].reshape(img_slice.shape)
        fig, ax = plt.subplots()
        ax.imshow(segmented_img, cmap='gray')
        ax.set_title("Segmentación K-Means")
        ax.axis('off')

        window = tk.Toplevel(self.master)
        window.title("Segmentación K-Means")
        canvas = FigureCanvasTkAgg(fig, master=window)
        canvas.draw()
        canvas.get_tk_widget().pack()

        save_button = tk.Button(window, text="Guardar como PNG", command=lambda: self.guardar_kmeans(segmented_img))
        save_button.pack(pady=10)

    def guardar_kmeans(self, data):
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if file_path:
            plt.imsave(file_path, data, cmap='gray')

def main():
    root = tk.Tk()
    app = NiiViewerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()