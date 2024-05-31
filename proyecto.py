import numpy as np
from scipy import sparse
import matplotlib.pyplot as plt
from scipy.sparse.linalg import factorized
from PIL import Image
from tkinter import filedialog, Tk

def main():
    # Deshabilitar la barra de herramientas
    plt.rcParams['toolbar'] = 'None'
    global seeds
    seeds = []
    # Función para manejar eventos del mouse
    def draw_circle(event):
        global seeds, prev_pos
        if event.button == 1: 
            color = 'blue'
            label = "F"
        elif event.button == 3:
            color = 'red'
            label = "B"
        else:
            return

        if event.name == 'button_press_event':
            prev_pos = (int(event.ydata), int(event.xdata))
        elif event.name == 'motion_notify_event' and prev_pos is not None:
            curr_pos = (int(event.ydata), int(event.xdata))
            plt.plot([prev_pos[1], curr_pos[1]], [prev_pos[0], curr_pos[0]], color=color)
            seeds.append((curr_pos, label))
            prev_pos = curr_pos

        plt.draw()

    # Cargar la imagen
    file_path = filedialog.askopenfilename(title="Seleccionar imagen", filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")])
    img = np.array(Image.open('imagen2.jpg').convert("L"))
    imgv = np.array(Image.open(file_path))


    # Crear una ventana y asociar la función de manejo de eventos del mouse
    fig, ax = plt.subplots()
    ax.imshow(imgv)
    ax.set_title('Cierra esta ventana luego de marcar las semillas.\nClick izquierdo foreground, click derecho  background')
    ax.axis('off')  # Para quitar los ejes
    
    prev_pos = None
    plt.connect('button_press_event', draw_circle)
    plt.connect('motion_notify_event', draw_circle)
    plt.axis('off')
    plt.show()


    hH, wW = img.shape
    numeracion = np.arange(hH * wW).reshape(hH,wW)
    # print("Dimensiones de la imagen:", hH, "x", wW)
    # print("Coordenadas de las semillas:", seeds)

    # Función para calcular la mediana de las diferencias de características
    def compute_sigma(img):
        hH, wW = img.shape
        sigma = 0
        aa=[]

        for i in range(hH):
            for j in range(wW):
                neighbors = [
                    (i - 1, j), (i + 1, j),
                    (i, j - 1), (i, j + 1)
                ]
                for ni, nj in neighbors:
                    if 0 <= ni < hH and 0 <= nj < wW:
                        sigma = max(sigma, np.abs(img[i, j] - img[ni, nj]))
                        aa.append( np.abs(img[i, j] - img[ni, nj]))
        return sigma

    # Uso de la función compute_sigma
    sigmaF = compute_sigma(img)
    # print("Sigma calculado:", sigmaF)

    # Función para calcular la afinidad entre dos píxeles
    def compute_affinity(pixel1, pixel2, sigma, epsilon):
        return np.exp(-epsilon * ((pixel1 - pixel2) ** 2).sum() / sigma)

    # Función para calcular los pesos de las coordenadas del laplaciano
    def affinity_matrixF(img):
        weights = sparse.lil_matrix((hH * wW, hH * wW))
        sigma = compute_sigma(img)
        for i in range(hH):
            for j in range(wW):
                idx = i * wW + j
                for ni, nj in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)):
                    if 0 <= ni < hH and 0 <= nj < wW:
                        weights[idx, ni * wW + nj] = compute_affinity(img[i, j], img[ni, nj], sigma, 10e-6)
        return weights

    # Construir el grafo de afinidad
    affinity_matrix = affinity_matrixF(img)
    W = affinity_matrix.toarray()
    D = sparse.diags(np.sum(W, axis=1))
    L = D - W

    mult_lap = L.dot(L)

    Is = sparse.lil_matrix((hH * wW, hH * wW))
    b = np.zeros(hH * wW)
    for (i, j), label in seeds:
        inij = numeracion[i,j]
        Is[inij, inij] = 1
        b[inij] = -1 if label == 'B' else 1
    A = sparse.csr_matrix(Is + mult_lap)
    solve = factorized(A)
    soluc = solve(b)
    soluc2 = soluc.reshape((hH, wW))

    xB=-1
    xF=1
    # Establecer el umbral de acuerdo con la ecuación 3
    umbral = (xB + xF) / 2
    # Crear la imagen binaria basada en el umbral
    binary_image = np.where(soluc2 >= umbral, img, 0)
    plt.imshow(binary_image, cmap='gray')
    plt.axis('off')
    plt.show()
