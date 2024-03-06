import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Rectangle
import nibabel as nib
from tkinter import ttk

class NIIViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Proyecto")

        # Ventana 1: Mostrar archivo cargado y botones
        self.canvas1 = tk.Canvas(root)
        self.fig1, self.ax1 = plt.subplots()
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=self.root)
        self.canvas1.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.rect1 = Rectangle((0, 0), 1, 1, fill=None, edgecolor='gray')
        self.ax1.add_patch(self.rect1)
        self.ax1.axis("off")
        self.save_button = tk.Button(self.root, text="Guardar", command=self.save_nii)
        # self.save_button.pack()
        self.segment_button = tk.Button(self.root, text="Segmentación", command=self.segment_dialog, height=5)
        self.segment_button.pack(fill=tk.X, expand=True)
        self.show_nii()

    def show_nii(self):
        file_path = filedialog.askopenfilename(filetypes=[("NII files", "*.nii")])
        if file_path:
            self.img = nib.load(file_path)
            self.data = self.img.get_fdata()
            self.update_plot1()
            self.cid_press1 = self.canvas1.mpl_connect('button_press_event', self.on_click1)

    def update_plot1(self):
        self.slice_num1 = self.data.shape[-1] // 2
        self.slice_data1 = np.rot90(self.data[:, :, self.slice_num1])
        self.ax1.imshow(self.slice_data1, cmap="gray")
        self.canvas1.draw_idle()

    def on_click1(self, event):
        x, y = int(event.xdata), int(event.ydata)
        self.rect1.set_xy((x - 10, y - 10))
        self.rect1.set_width(20)
        self.rect1.set_height(20)
        self.fig1.canvas.draw()
        self.canvas1.mpl_disconnect(self.cid_press1) # Desconectar la conexión anterior
        self.cid_move1 = self.canvas1.mpl_connect('motion_notify_event', self.on_motion1)
        self.cid_release1 = self.canvas1.mpl_connect('button_release_event', self.on_release1)

        self.xs1 = [x]
        self.ys1 = [y]

    def on_motion1(self, event):
        if event.inaxes and event.button == 1:
            x, y = int(event.xdata), int(event.ydata)
            self.xs1.append(x)
            self.ys1.append(y)
            self.ax1.plot(self.xs1[-2:], self.ys1[-2:], color='red')
            self.canvas1.draw()

    def on_release1(self, event):
        if event.button == 1:
            self.canvas1.mpl_disconnect(self.cid_move1)
            self.canvas1.mpl_disconnect(self.cid_release1)
            self.cid_press1 = self.canvas1.mpl_connect('button_press_event', self.on_click1)

    def segment_dialog(self):
        self.segment_dialog = tk.Toplevel(self.root)
        self.segment_dialog.title("Seleccione un método de segmentación")

        frame = tk.Frame(self.segment_dialog)
        frame.pack()

        threshold_button = tk.Button(frame, text="Umbral", command=self.segment_threshold, width=15, height=2)
        threshold_button.pack(side=tk.LEFT, padx=5,pady= 10)

        isodata_button = tk.Button(frame, text="Isodata", command=self.segment_isodata, width=15, height=2)
        isodata_button.pack(side=tk.LEFT, padx=5,pady= 10)

        region_growing_button = tk.Button(frame, text="Crecimiento de Regiones", command=self.segment_region_growing, width=20, height=2)
        region_growing_button.pack(side=tk.LEFT, padx=5,pady= 10)

        kmeans_button = tk.Button(frame, text="K-Means", command=self.segment_kmeans, width=15, height=2)
        kmeans_button.pack(side=tk.LEFT, padx=5,pady= 10)


    def show_isodata_segmentation(self):
        isodata_data = self.apply_isodata_segmentation()
        self.ax2.imshow(isodata_data, cmap="gray")
        
        # Agregar subplot para el histograma
        self.fig2, (self.ax_hist, self.ax2) = plt.subplots(2, 1)
        hist, bins = np.histogram(self.slice_data1.flatten(), bins=256, range=(0,256))
        self.ax_hist.bar(bins[:-1], hist, width=1)
        
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.threshold_dialog)
        self.canvas2.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.ax2.axis("off")
        self.canvas2.draw_idle()

    def apply_isodata_segmentation(self):
        # Calcular el histograma de la imagen
        hist, bins = np.histogram(self.slice_data1.flatten(), bins=256, range=(0,256))

        # Calcular el umbral inicial
        threshold = 128

        # Iterar hasta que el umbral converja
        while True:
            # Calcular las medias de las dos clases
            mean1 = np.mean(self.slice_data1[self.slice_data1 <= threshold])
            mean2 = np.mean(self.slice_data1[self.slice_data1 > threshold])

            # Calcular el nuevo umbral como el promedio de las dos medias
            new_threshold = (mean1 + mean2) / 2

            # Si el nuevo umbral es igual al umbral anterior, detener la iteración
            if new_threshold == threshold:
                break

            # Actualizar el umbral
            threshold = new_threshold

        # Aplicar el umbral a la imagen
        segmented_data = np.where(self.slice_data1 > threshold, 255, 0)

        return segmented_data


    def segment_threshold(self):
        self.threshold_dialog = tk.Toplevel(self.root)
        self.threshold_dialog.title("Segmentación por Umbral")

        self.threshold_slider = ttk.Scale(self.threshold_dialog, from_=0, to=255, orient="horizontal", command=self.update_threshold, value=255)
        self.threshold_slider.pack()

        self.canvas2 = tk.Canvas(self.threshold_dialog)
        self.fig2, self.ax2 = plt.subplots()
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.threshold_dialog)
        self.canvas2.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.rect2 = Rectangle((0, 0), 1, 1, fill=None, edgecolor='gray')
        self.ax2.add_patch(self.rect2)
        self.ax2.axis("off")

        self.update_threshold(self.threshold_slider.get())

    def update_threshold(self, value):
        threshold_value = int(float(value))
        self.threshold_value = threshold_value
        thresholded_data = np.where(self.slice_data1 > self.threshold_value, 255, 0)
        self.ax2.imshow(thresholded_data, cmap="gray")
        self.canvas2.draw_idle()

    def segment_isodata(self):
        self.threshold_dialog = tk.Toplevel(self.root)
        self.threshold_dialog.title("Segmentación Isodata")

        self.canvas2 = tk.Canvas(self.threshold_dialog)
        self.fig2, self.ax2 = plt.subplots()
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.threshold_dialog)
        self.canvas2.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.rect2 = Rectangle((0, 0), 1, 1, fill=None, edgecolor='gray')
        self.ax2.add_patch(self.rect2)
        self.ax2.axis("off")

        self.show_isodata_segmentation()

    def segment_region_growing(self):
        messagebox.showinfo("Segmentación", "Método de Segmentación: Crecimiento de Regiones")

    def segment_kmeans(self):
        messagebox.showinfo("Segmentación", "Método de Segmentación: K-Means")

    def save_nii(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".nii", filetypes=[("NII files", "*.nii")])
        if file_path:
            self.data[:, :, self.slice_num1] = np.rot90(self.slice_data1)
            new_img = nib.Nifti1Image(self.data, self.img.affine)
            nib.save(new_img, file_path)

if __name__ == "__main__":
    root = tk.Tk()
    app = NIIViewerApp(root)
    root.mainloop()
