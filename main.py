import tkinter as tk
from tkinter import filedialog
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
        self.canvas = tk.Canvas(root)
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.rect = Rectangle((0, 0), 1, 1, fill=None, edgecolor='gray')
        self.ax.add_patch(self.rect)
        self.ax.axis("off")
        self.save_button = tk.Button(self.root, text="Guardar", command=self.save_nii)
        self.save_button.pack()
        self.threshold_slider = ttk.Scale(self.root, from_=0, to=255, orient="horizontal", command=self.update_threshold)
        self.threshold_slider.pack()
        self.threshold_value = 128  # Inicialización del valor de umbral predeterminado
        self.show_nii()

    def show_nii(self):
        file_path = filedialog.askopenfilename(filetypes=[("NII files", "*.nii")])
        if file_path:
            self.img = nib.load(file_path)
            self.data = self.img.get_fdata()
            self.update_plot()
            self.cid_press = self.canvas.mpl_connect('button_press_event', self.on_click)

    def update_plot(self):
        self.slice_num = self.data.shape[-1] // 2
        self.slice_data = np.rot90(self.data[:, :, self.slice_num])

        # Aplicar segmentación por umbral
        thresholded_data = np.where(self.slice_data > self.threshold_value, 255, 0)

        self.ax.imshow(thresholded_data, cmap="gray")
        self.canvas.draw_idle()

    def on_click(self, event):
        x, y = int(event.xdata), int(event.ydata)
        self.rect.set_xy((x - 10, y - 10))
        self.rect.set_width(20)
        self.rect.set_height(20)
        self.fig.canvas.draw()
        self.canvas.mpl_disconnect(self.cid_press) # Desconectar la conexión anterior
        self.cid_move = self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.cid_release = self.canvas.mpl_connect('button_release_event', self.on_release)

        self.xs = [x]
        self.ys = [y]

    def on_motion(self, event):
        if event.inaxes and event.button == 1:
            x, y = int(event.xdata), int(event.ydata)
            self.xs.append(x)
            self.ys.append(y)
            self.ax.plot(self.xs[-2:], self.ys[-2:], color='red')
            self.canvas.draw()

    def on_release(self, event):
        if event.button == 1:
            self.canvas.mpl_disconnect(self.cid_move)
            self.canvas.mpl_disconnect(self.cid_release)
            self.cid_press = self.canvas.mpl_connect('button_press_event', self.on_click)

    def update_threshold(self, value):
        threshold_value = int(float(value)) # Convertir el valor a un número flotante y luego a un número entero
        self.threshold_value = threshold_value
        self.update_plot()

    def save_nii(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".nii", filetypes=[("NII files", "*.nii")])
        if file_path:
            self.data[:, :, self.slice_num] = np.rot90(self.slice_data)
            new_img = nib.Nifti1Image(self.data, self.img.affine)
            nib.save(new_img, file_path)

if __name__ == "__main__":
    root = tk.Tk()
    app = NIIViewerApp(root)
    root.mainloop()
