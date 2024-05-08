import tkinter as tk
from tkinter import filedialog, messagebox
import nibabel as nib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import scipy.ndimage
from scipy.signal import convolve2d
import SimpleITK as sitk

class NiiViewerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Segmentaciones")
        self.frame = tk.Frame(self.master)
        self.frame.pack()
        self.file_path = "file.nii" 
        self.img = nib.load(self.file_path)
        self.img_data = self.img.get_fdata() 
        self.file_path2 = "file2.nii" 
        self.img2 = nib.load(self.file_path2)
        self.img_data2 = self.img2.get_fdata() 
        self.update_delay = 100 
        self.update_slice_id = None
        self.z_slider = tk.Scale(self.frame, from_=0, to=1, orient=tk.HORIZONTAL, resolution=1, command=self.update_slice)
        self.z_slider.pack()
        self.z_slider.config(to=self.img_data.shape[2] - 1)
        self.z_slider.set(self.img_data.shape[2] // 2)
        self.canvas = None
        self.cid_press1 = None
        self.process_button = tk.Button(self.frame, text="Bordes/Registro", command=self.optionsProcess)
        self.process_button.pack()
        self.segmented_img = None
        self.segmented_canvas = None
        self.segmented_z_slider = None
        self.trazos = [] 
        self.trazos_guardados = False

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

    def optionsProcess(self):
        dialog = tk.Toplevel(self.master)
        dialog.title("Opciones")
        frame = tk.Frame(dialog)
        frame.pack()
        def bordersf():
            dialog.destroy()
            self.borders()
        def registerf():
            dialog.destroy()
            self.registerf()
        
        bordersf_button = tk.Button(frame, text="Bordes", command=bordersf, width=15, height=2)
        bordersf_button.pack(side=tk.LEFT, padx=5, pady=10)
        register_button = tk.Button(frame, text="Registro", command=registerf, width=15, height=2)
        register_button.pack(side=tk.LEFT, padx=5, pady=10)
    
    
    def borders(self):
        # Define los kernels para detectar bordes
        kernel_x = np.array([[0, 0, 0], [-1, 0, 1], [0, 0, 0]]) / 2
        kernel_y = np.array([[0, -1, 0], [0, 0, 0], [0, 1, 0]]) / 2

        # Realiza la convolución para detectar bordes horizontales y verticales
        img_filt_x = scipy.ndimage.convolve(self.img_data[:, :, self.z_slice], kernel_x)
        img_filt_y = scipy.ndimage.convolve(self.img_data[:, :, self.z_slice], kernel_y)

        dxx= scipy.ndimage.convolve(img_filt_x, kernel_x )
        dxy= scipy.ndimage.convolve(img_filt_x, kernel_y )
        dyy= scipy.ndimage.convolve(img_filt_y, kernel_y)

        # Calcula la magnitud de los bordes
        final = np.sqrt(img_filt_x ** 2 + img_filt_y ** 2)
        final_thresholded = np.sqrt(img_filt_x ** 2 + img_filt_y ** 2) > 57
        final_thresholdedII = np.sqrt(dxx ** 2 + dxy ** 2 + dyy ** 2) 

        # Muestra las imágenes resultantes
        dialog = tk.Toplevel(self.master)
        dialog.title("Imagen con bordes")
        frame = tk.Frame(dialog)
        frame.pack()

        fig, axes = plt.subplots(2, 2, figsize=(10, 8))

        # Configuración de la primera fila
        ax1 = axes[0, 0]
        ax1.imshow(final, cmap='gray')
        ax1.set_title("Imagen con bordes(Primera derivada)")
        ax1.axis('off')

        ax2 = axes[0, 1]
        ax2.imshow(final_thresholded)
        ax2.set_title("Primera derivada umbralizada")
        ax2.axis('off')

        # Oculta el tercer subplot vacío
        axes[1, 0].axis('off')
        axes[1, 1].axis('off')

        # Configuración de la segunda fila
        ax3 = fig.add_subplot(212)
        ax3.imshow(final_thresholdedII, cmap='gray')
        ax3.set_title("Segunda derivada")
        ax3.axis('off')

        # Ajusta el espacio entre subplots
        plt.tight_layout(pad=3.0)

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack()   
        
    
    def registerf(self):
        # Abre un diálogo para seleccionar el archivo de imagen a registrar
        file_path_registration = filedialog.askopenfilename(title="Seleccionar archivo para registro", filetypes=[("NIfTI files", "*.nii")])
        if file_path_registration:
            # Carga la imagen para el registro
            img_registration = nib.load(file_path_registration)
            img_data_registration = img_registration.get_fdata()

            # Realiza el registro utilizando SimpleITK
            fixed_image = sitk.GetImageFromArray(self.img_data)
            moving_image = sitk.GetImageFromArray(img_data_registration)

            # Configura el registro utilizando el método de registro de intensidad mutual
            registration_method = sitk.ImageRegistrationMethod()
            registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
            registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
            registration_method.SetMetricSamplingPercentage(0.01)
            registration_method.SetInterpolator(sitk.sitkLinear)

            # Configura el optimizador
            registration_method.SetOptimizerAsGradientDescent(learningRate=1.0, numberOfIterations=100, estimateLearningRate=registration_method.Never)
            registration_method.SetOptimizerScalesFromPhysicalShift()

            # Realiza el registro
            final_transform = registration_method.Execute(fixed_image, moving_image)

            # Muestra la imagen original y la registrada en la misma ventana
            dialog = tk.Toplevel(self.master)
            dialog.title("Imagenes Superpuestas")
            frame = tk.Frame(dialog)
            frame.pack()

            fig_registered = plt.figure()
            ax_registered = fig_registered.add_subplot(111)

            # Muestra la imagen original
            ax_registered.imshow(self.img_data[:, :, self.z_slice], cmap='gray')

            # Aplica la transformación a la imagen móvil
            registered_image = sitk.Resample(moving_image, fixed_image, final_transform, sitk.sitkLinear, 0.0, moving_image.GetPixelID())

            # Obtiene los datos de la imagen registrada
            registered_image_data = sitk.GetArrayFromImage(registered_image)

            # Muestra la imagen registrada superpuesta encima de la original con transparencia
            ax_registered.imshow(registered_image_data[:, :, self.z_slice], cmap='viridis', alpha=0.3)

            ax_registered.set_title("Imagenes Superpuestas")
            ax_registered.axis('off')
            fig_registered.tight_layout()
            canvas_registered = FigureCanvasTkAgg(fig_registered, master=dialog)
            canvas_registered.draw()
            canvas_registered.get_tk_widget().pack()


    
        

def main():
    root = tk.Tk()
    app = NiiViewerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
