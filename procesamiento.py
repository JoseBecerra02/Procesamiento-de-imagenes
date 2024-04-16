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

   
    def optionsProcess(self):
        print(np.median([2, 3, 3, 5, 8, 10, 11]))
        print(2+3+3+5+8+10+11)
        print((2+3+3+5+8+10+11)/7)
        print(np.mean([2, 3, 3, 5, 8, 10, 11]))
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
            dialog = tk.Toplevel(self.master)
            dialog.title("Filtro de Media")
            frame = tk.Frame(dialog)
            frame.pack()
            kernel =  0

            # Etiqueta y variable para seleccionar el tamaño del kernel
            kernel_size_label = tk.Label(frame, text="Tamaño del Kernel:")
            kernel_size_label.grid(row=0, column=0, padx=5, pady=5)
            self.kernel_size_var = tk.StringVar()
            self.kernel_size_var.set("3x3")  # Valor por defecto

            # Opciones de tamaño del kernel
            kernel_size_options = ["3x3", "5x5", "10x10"]
            kernel_size_menu = tk.OptionMenu(frame, self.kernel_size_var, *kernel_size_options)
            kernel_size_menu.grid(row=0, column=1, padx=5, pady=5)
            def adada():
                if(self.kernel_size_var.get()=="3x3"):
                    kernel=3
                elif(self.kernel_size_var.get()=="5x5"):
                    kernel=5
                else:
                    kernel=10

                self.mean(kernel)               

            # Botón para aplicar el filtro de media con el tamaño seleccionado
            apply_button = tk.Button(frame, text="Aplicar", command=adada)
            apply_button.grid(row=1, column=0, columnspan=2, pady=10)
        def median():
            dialog = tk.Toplevel(self.master)
            dialog.title("Filtro de Media")
            frame = tk.Frame(dialog)
            frame.pack()
            kernel =  0

            # Etiqueta y variable para seleccionar el tamaño del kernel
            kernel_size_label = tk.Label(frame, text="Tamaño del Kernel:")
            kernel_size_label.grid(row=0, column=0, padx=5, pady=5)
            self.kernel_size_var = tk.StringVar()
            self.kernel_size_var.set("3x3")  # Valor por defecto

            # Opciones de tamaño del kernel
            kernel_size_options = ["3x3", "5x5", "10x10"]
            kernel_size_menu = tk.OptionMenu(frame, self.kernel_size_var, *kernel_size_options)
            kernel_size_menu.grid(row=0, column=1, padx=5, pady=5)
            def adada():
                if(self.kernel_size_var.get()=="3x3"):
                    kernel=3
                elif(self.kernel_size_var.get()=="5x5"):
                    kernel=5
                else:
                    kernel=10

                self.median(kernel)               

            # Botón para aplicar el filtro de media con el tamaño seleccionado
            apply_button = tk.Button(frame, text="Aplicar", command=adada)
            apply_button.grid(row=1, column=0, columnspan=2, pady=10)
            
        histogram_button = tk.Button(frame, text="Histograma", command=histogram, width=15, height=2)
        histogram_button.pack(side=tk.LEFT, padx=5, pady=10)
        whitestraping_button = tk.Button(frame, text="White stripe", command=white, width=20, height=2)
        whitestraping_button.pack(side=tk.LEFT, padx=5, pady=10)
        intensity_button = tk.Button(frame, text="Intesity rescaller", command=intensity, width=15, height=2)
        intensity_button.pack(side=tk.LEFT, padx=5, pady=10)
        zindex_button = tk.Button(frame, text="Zscore", command=zindex, width=15, height=2)
        zindex_button.pack(side=tk.LEFT, padx=5, pady=10)
        mean_button = tk.Button(frame, text="Mean", command=mean, width=15, height=2)
        mean_button.pack(side=tk.LEFT, padx=5, pady=10)
        median_button = tk.Button(frame, text="Median", command=median, width=15, height=2)
        median_button.pack(side=tk.LEFT, padx=5, pady=10)
    
    def histogram(self):
        num_percentiles = 10
    
        x = np.linspace(5,95,num_percentiles)
        y = np.percentile(self.img_data2.flatten(), x)
        
        trozos = []
        for i in range(1 , len(y)):
            m = (y[i]-y[i-1])/(x[i]-x[i-1])
            b = y[i-1]- m * x[i-1]
            fx = lambda x : m*x + b
            trozos.append([m,b,fx])

        x1 = np.linspace(5,95,num_percentiles)
        y1= np.percentile(self.img_data.flatten(), x)

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

        dialog = tk.Toplevel(self.master)
        fig_new_array = plt.figure()
        ax_new_array = fig_new_array.add_subplot(111)
        ax_new_array.imshow(new_array[:, :, self.z_slice], cmap='gray') 
        ax_new_array.set_title("Histogram matching")
        ax_new_array.axis('off')
        fig_new_array.tight_layout()  
        canvas_new_array = FigureCanvasTkAgg(fig_new_array, master=dialog)
        canvas_new_array.draw()
        canvas_new_array.get_tk_widget().pack()

    def intensity(self):
        max = np.max(self.img_data)
        min = np.min(self.img_data)
        final = (self.img_data - min) / (max - min)

        dialog = tk.Toplevel(self.master)
        dialog.title("Intensity rescaller")
        frame = tk.Frame(dialog)
        frame.pack()
        fig_new_array = plt.figure()
        ax_new_array = fig_new_array.add_subplot(111)
        ax_new_array.imshow(final[:, :, self.z_slice], cmap='gray')
        ax_new_array.set_title("Intensity rescaller")
        ax_new_array.axis('off')
        fig_new_array.tight_layout()  
        canvas_new_array = FigureCanvasTkAgg(fig_new_array, master=dialog)
        canvas_new_array.draw()
        canvas_new_array.get_tk_widget().pack()

    def white(self):
        def peaks_f(histogram, threshold=100):
            peaks = []
            for i in range(1, len(hist) - 1):
                if histogram[i] > histogram[i - 1] and histogram[i] > histogram[i + 1] and histogram[i] > threshold:
                    peaks.append(i)
            return peaks

        hist, bin_edges = np.histogram(self.img_data.flatten(), bins=100)
        peaks = peaks_f(hist)
        peaks_values = bin_edges[peaks]

        image_rescaled = self.img_data / peaks_values[-1]

        dialog = tk.Toplevel(self.master)
        dialog.title("White stipe")
        frame = tk.Frame(dialog)
        frame.pack()
        fig_new_array = plt.figure()
        ax_new_array = fig_new_array.add_subplot(111)
        ax_new_array.imshow(image_rescaled[:, :, self.z_slice], cmap='gray') 
        ax_new_array.set_title("Imagen después de white stipe")
        ax_new_array.axis('off')
        fig_new_array.tight_layout()
        canvas_new_array = FigureCanvasTkAgg(fig_new_array, master=frame)
        canvas_new_array.draw()
        canvas_new_array.get_tk_widget().pack()

        

        def show_histograms():
            min =  0
            filtered_reference_image = self.img_data.flatten()[self.img_data.flatten() > min]
            filtered_image_rescaled = image_rescaled.flatten()[image_rescaled.flatten() > min]
            dialog = tk.Toplevel(self.master)
            dialog.title("Histogramas")
            
            # Mostrar histograma original
            fig_hist_original = plt.figure(figsize=(14, 6))
            ax_hist_original = fig_hist_original.add_subplot(121)
            ax_hist_original.hist(filtered_reference_image.flatten(), bins=100, color='red', alpha=0.7)
            ax_hist_original.set_title("Histograma original")
            ax_hist_original.set_xlabel("Intensidad")
            ax_hist_original.set_ylabel("Frecuencia")
            

            # Mostrar histograma después de white stipe
            ax_hist = fig_hist_original.add_subplot(122)
            ax_hist.hist(filtered_image_rescaled.flatten(), bins=100, color='blue', alpha=0.7)
            ax_hist.set_title("Histograma después white stipe")
            ax_hist.set_xlabel("Intensidad")
            ax_hist.set_ylabel("Frecuencia")
            

            canvas_hist_original = FigureCanvasTkAgg(fig_hist_original, master=dialog)
            canvas_hist_original.draw()
            canvas_hist_original.get_tk_widget().pack()
        show_hist_button = tk.Button(frame, text="Mostrar Histogramas", command=show_histograms)
        show_hist_button.pack()

    def zscore(self):
        img = self.img_data

        mean = img[img > 10].mean()
        standard_deviation_value = img[img > 10].std()

        image_rescaled = (img - mean) / (standard_deviation_value)


        dialog = tk.Toplevel(self.master)
        dialog.title("Z-Score")
        frame = tk.Frame(dialog)
        frame.pack()
        fig_new_array = plt.figure()
        ax_new_array = fig_new_array.add_subplot(111)
        ax_new_array.imshow(image_rescaled[:, :, self.z_slice], cmap='gray')
        ax_new_array.set_title("Z-Score")
        ax_new_array.axis('off')
        fig_new_array.tight_layout()
        canvas_new_array = FigureCanvasTkAgg(fig_new_array, master=dialog)
        canvas_new_array.draw()
        canvas_new_array.get_tk_widget().pack()


    def mean(self,kernel_size):
        # Crea una nueva imagen para almacenar la imagen filtrada
        filtered_image = np.zeros_like(self.img_data)

        # Aplica el filtro de media a la imagen
        for x in range(self.img_data.shape[0]):
            for y in range(self.img_data.shape[1]):
                for z in range(self.img_data.shape[2]):
                    # Calcula el valor promedio de los píxeles dentro del kernel
                    pixel_sum = 0
                    count = 0
                    for i in range(-kernel_size // 2, kernel_size // 2 + 1):
                        for j in range(-kernel_size // 2, kernel_size // 2 + 1):
                            if (x + i >= 0 and x + i < self.img_data.shape[0] and
                                y + j >= 0 and y + j < self.img_data.shape[1] and
                                z >= 0 and z < self.img_data.shape[2]):
                                pixel_sum += self.img_data[x + i, y + j, z]
                                count += 1
                    filtered_image[x, y, z] = pixel_sum / count

        # Crea una nueva ventana para mostrar la imagen filtrada
        dialog = tk.Toplevel(self.master)
        dialog.title("Filtro de Media")
        frame = tk.Frame(dialog)
        frame.pack()

        # Visualiza la imagen filtrada
        fig_new_array = plt.figure()
        ax_new_array = fig_new_array.add_subplot(111)
        ax_new_array.imshow(filtered_image[:, :, self.z_slice], cmap='gray')
        ax_new_array.set_title("Imagen después del Filtro de Media")
        ax_new_array.axis('off')
        fig_new_array.tight_layout()
        canvas_new_array = FigureCanvasTkAgg(fig_new_array, master=dialog)
        canvas_new_array.draw()
        canvas_new_array.get_tk_widget().pack()

    def median(self, kernel_size):
        # Crea una nueva imagen para almacenar la imagen filtrada
        filtered_image = np.zeros_like(self.img_data)

        # Aplica el filtro de mediana a la imagen
        for x in range(self.img_data.shape[0]):
            for y in range(self.img_data.shape[1]):
                for z in range(self.img_data.shape[2]):
                    # Recopila los valores de intensidad de los píxeles dentro del kernel
                    values = []
                    for i in range(-kernel_size // 2, kernel_size // 2 + 1):
                        for j in range(-kernel_size // 2, kernel_size // 2 + 1):
                            if (x + i >= 0 and x + i < self.img_data.shape[0] and
                                y + j >= 0 and y + j < self.img_data.shape[1] and
                                z >= 0 and z < self.img_data.shape[2]):
                                values.append(self.img_data[x + i, y + j, z])
                    
                    # Calcula el valor mediano de los píxeles dentro del kernel
                    filtered_image[x, y, z] = np.median(values)

        # Crea una nueva ventana para mostrar la imagen filtrada
        dialog = tk.Toplevel(self.master)
        dialog.title("Filtro de Mediana")
        frame = tk.Frame(dialog)
        frame.pack()

        # Visualiza la imagen filtrada
        fig_new_array = plt.figure()
        ax_new_array = fig_new_array.add_subplot(111)
        ax_new_array.imshow(filtered_image[:, :, self.z_slice], cmap='gray')
        ax_new_array.set_title("Imagen después del Filtro de Mediana")
        ax_new_array.axis('off')
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
