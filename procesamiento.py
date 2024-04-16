import tkinter as tk
from tkinter import filedialog, messagebox
import nibabel as nib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from scipy import stats

class NiiViewerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Segmentaciones")
        self.frame = tk.Frame(self.master)
        self.frame.pack()
        self.file_path = "file.nii"  # Cambia el nombre del archivo según sea necesario
        self.img = nib.load(self.file_path)
        self.img_data = self.img.get_fdata() 
        self.file_path2 = "file2.nii"  # Cambia el nombre del archivo según sea necesario
        self.img2 = nib.load(self.file_path2)
        self.img_data2 = self.img2.get_fdata() 
        self.update_delay = 100 
        self.update_slice_id = None
        self.z_slider = tk.Scale(self.frame, from_=0, to=1, orient=tk.HORIZONTAL, resolution=1, command=self.update_slice)
        self.z_slider.pack()
        self.z_slider.config(to=self.img_data.shape[2] - 1)
        self.z_slider.set(self.img_data.shape[2] // 2)
        self.z_slider.bind("<MouseWheel>", self.desplazamiento)
        self.canvas = None
        self.cid_press1 = None
        self.process_button = tk.Button(self.frame, text="Procesamiento", command=self.optionsProcess)
        self.process_button.pack()
        self.segmented_img = None
        self.segmented_canvas = None
        self.segmented_z_slider = None
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
            # self.canvas.mpl_connect('button_press_event', self.on_press)
            # self.canvas.mpl_connect('motion_notify_event', self.on_motion)
            # Dibujar trazos guardados si están disponibles
            if self.trazos_guardados:
                self.dibujar_trazos()

    def desplazamiento(self, event):
        if event.delta > 0:
            self.z_slider.set(self.z_slider.get() + 1)
        else:
            self.z_slider.set(self.z_slider.get() - 1)

    def options(self):
        pass
    
    def optionsProcess(self):
        dialog = tk.Toplevel(self.master)
        dialog.title("Opciones de Segmentación")
        frame = tk.Frame(dialog)
        frame.pack()
        def histogram():
            dialog.destroy()
            self.histogram()
        def white():
            dialog.destroy()
            self.white()
        def intensity():
            dialog.destroy()
            self.intensity()
        def zindex():
            dialog.destroy()
            self.zscore()
        def mean():
            dialog.destroy()
            self.mean()
        def median():
            dialog.destroy()
            self.median()
        histogram_button = tk.Button(frame, text="Histograma", command=histogram, width=15, height=2)
        histogram_button.pack(side=tk.LEFT, padx=5, pady=10)
        whitestraping_button = tk.Button(frame, text="White stripe", command=white, width=20, height=2)
        whitestraping_button.pack(side=tk.LEFT, padx=5, pady=10)
        intensity_button = tk.Button(frame, text="Intesity rescaller", command=intensity, width=15, height=2)
        intensity_button.pack(side=tk.LEFT, padx=5, pady=10)
        zindex_button = tk.Button(frame, text="Zscore", command=zindex, width=15, height=2)
        zindex_button.pack(side=tk.LEFT, padx=5, pady=10)
    
    def histogram(self):
        dialog = tk.Toplevel(self.master)
        num_percentiles = 10
    
        x = np.linspace(5,95,num_percentiles)
        y = np.percentile(self.img_data2.flatten(), x)
        
        trozos = []
        for i in range(1 , len(y)):
            m = (y[i]-y[i-1])/(x[i]-x[i-1])
            b = y[i-1]- m * x[i-1]
            fx = lambda x : m*x + b
            # Aquí puedes hacer lo que necesites con la función fx
            trozos.append([m,b,fx])
            # print(f"Para el trazo {i}, la función lineal es: y = {m} * x + {b} . {fx}")
        # print(trozos)


        # print("-"*100)
        # print(x)
        # print(y)
        # print(trozos)

        # print("")
        x1 = np.linspace(5,95,num_percentiles)
        y1= np.percentile(self.img_data.flatten(), x)
        # print(x1)
        # print(y1)

        percentile_value = 100  # Por ejemplo, calcularemos el percentil 50 (la mediana)
        percentile_image = np.percentile(self.img_data2, percentile_value)
        # print(f"El valor del percentil {percentile_value} de la imagen es: {percentile_image}")
        new_array = np.zeros_like(self.img_data)

        for x in range(self.img_data.shape[0]):
            for y in range(self.img_data.shape[1]):
                for z in range(self.img_data.shape[2]):
                    voxel_value_img1 = self.img_data[x, y, z]
                    
                    # Buscar el percentil correspondiente en la imagen 1
                    for i in range(len(x1)-1):
                        if voxel_value_img1 >= y1[i] and voxel_value_img1 < y1[i+1]:
                            percentile_img1 = x1[i]
                            percentile_position = np.where(x1 == percentile_img1)[0][0]
                            new_valor  = trozos[percentile_position-1][2](voxel_value_img1)
                            new_array[x, y, z] = new_valor
                            break
                        elif voxel_value_img1 >= y1[-1]:
                            percentile_img1 = x1[-1]
                            percentile_position = np.where(x1 == percentile_img1)[0][0]
                            new_valor  = trozos[percentile_position-1][2](voxel_value_img1)
                            new_array[x, y, z] = new_valor
                            break
                    else:
                        percentile_img1 = None
        # Mostrar new_array en un nuevo lienzo
        # print(self.img_data==new_array)
        fig_new_array = plt.figure()
        ax_new_array = fig_new_array.add_subplot(111)
        ax_new_array.imshow(new_array[:, :, self.z_slice], cmap='gray')  # Ajusta el cmap según corresponda
        ax_new_array.set_title("Histograma")
        ax_new_array.axis('off')

        # No necesitas llamar a tight_layout() en los ejes, llámalo en la figura
        fig_new_array.tight_layout()  

        canvas_new_array = FigureCanvasTkAgg(fig_new_array, master=dialog)
        canvas_new_array.draw()
        canvas_new_array.get_tk_widget().pack()

    def intensity(self):
        dialog = tk.Toplevel(self.master)
        dialog.title("Intensidad del Escalador")
        frame = tk.Frame(dialog)
        frame.pack()

        # Escalar la imagen actual
        max_intensity = np.max(self.img_data)
        min_intensity = np.min(self.img_data)
        scaled_img_data = (self.img_data - min_intensity) / (max_intensity - min_intensity)
        # print(scaled_img_data==self.img_data)
        # print(max_intensity)
        # print(min_intensity)

        fig_new_array = plt.figure()
        ax_new_array = fig_new_array.add_subplot(111)
        ax_new_array.imshow(scaled_img_data[:, :, self.z_slice], cmap='gray')  # Ajusta el cmap según corresponda
        ax_new_array.set_title("Histograma")
        ax_new_array.axis('off')

        # No necesitas llamar a tight_layout() en los ejes, llámalo en la figura
        fig_new_array.tight_layout()  

        canvas_new_array = FigureCanvasTkAgg(fig_new_array, master=dialog)
        canvas_new_array.draw()
        canvas_new_array.get_tk_widget().pack()

    def white(self):
        dialog = tk.Toplevel(self.master)
        dialog.title("stra")
        frame = tk.Frame(dialog)
        frame.pack()
        # Get reference image to standardise original image
        # path = os.path.abspath("./images/1/FLAIR.nii.gz")
        # reference_image = nib.load(path).get_fdata()

        def find_peaks_manual(hist, threshold=100):
            peaks = []
            for i in range(1, len(hist) - 1):
                if hist[i] > hist[i - 1] and hist[i] > hist[i + 1] and hist[i] > threshold:
                    peaks.append(i)
            return peaks

        reference_image = self.img_data
        

        # Create histogram
        hist, bin_edges = np.histogram(reference_image.flatten(), bins=100)

        # Find all the histogram peaks
        peaks = find_peaks_manual(hist)
        peaks_values = bin_edges[peaks]

        # Rescaled image with the second peak (White matter)
        image_rescaled = self.img_data / peaks_values[1]

        print(self.img_data[88,:,:])
        print("-"*50)
        print(image_rescaled[88,:,:])

        fig_new_array = plt.figure()
        ax_new_array = fig_new_array.add_subplot(111)
        ax_new_array.imshow(image_rescaled[:, :, self.z_slice], cmap='gray')  # Ajusta el cmap según corresponda
        ax_new_array.set_title("Histograma")
        ax_new_array.axis('off')

        # No necesitas llamar a tight_layout() en los ejes, llámalo en la figura
        fig_new_array.tight_layout()  

        canvas_new_array = FigureCanvasTkAgg(fig_new_array, master=dialog)
        canvas_new_array.draw()
        canvas_new_array.get_tk_widget().pack()
    def zscore(self):
        dialog = tk.Toplevel(self.master)
        dialog.title("Intensidad del Escalador")
        frame = tk.Frame(dialog)
        frame.pack()
        img = self.img_data

        mean_value = img[img > 10].mean()
        standard_deviation_value = img[img > 10].std()

        if np.std(img) == 0:
            image_rescaled = img
        else:
            # image_standardized = (image - np.mean(image)) / np.std(image)
            image_rescaled = (img - mean_value) / (standard_deviation_value)
        print(self.img_data[80,:,:])
        print("-"*100)
        print(image_rescaled[80,:,:])
        fig_new_array = plt.figure()
        ax_new_array = fig_new_array.add_subplot(111)
        ax_new_array.imshow(image_rescaled[:, :, self.z_slice], cmap='gray')  # Ajusta el cmap según corresponda
        ax_new_array.set_title("Histograma")
        ax_new_array.axis('off')

        # No necesitas llamar a tight_layout() en los ejes, llámalo en la figura
        fig_new_array.tight_layout()  

        canvas_new_array = FigureCanvasTkAgg(fig_new_array, master=dialog)
        canvas_new_array.draw()
        canvas_new_array.get_tk_widget().pack()
        

def main():
    root = tk.Tk()
    app = NiiViewerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
