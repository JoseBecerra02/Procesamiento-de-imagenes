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
        self.save_button.pack()
        self.segment_button = tk.Button(self.root, text="Segmentación", command=self.segment_dialog)
        self.segment_button.pack()
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

        threshold_button = tk.Button(self.segment_dialog, text="Umbral", command=self.segment_threshold)
        threshold_button.pack()

        isodata_button = tk.Button(self.segment_dialog, text="Isodata", command=self.show_hello)
        isodata_button.pack()

        region_growing_button = tk.Button(self.segment_dialog, text="Crecimiento de Regiones", command=self.segment_region_growing)
        region_growing_button.pack()

        kmeans_button = tk.Button(self.segment_dialog, text="K-Means", command=self.segment_kmeans)
        kmeans_button.pack()

    def show_hello(self):
        messagebox.showinfo("Hola", "¡Hola!")

    def segment_threshold(self):
        self.threshold_dialog = tk.Toplevel(self.root)
        self.threshold_dialog.title("Segmentación por Umbral")

        self.threshold_slider = ttk.Scale(self.threshold_dialog, from_=0, to=255, orient="horizontal", command=self.update_threshold)
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
        messagebox.showinfo("Segmentación", "Método de Segmentación: Isodata")

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
