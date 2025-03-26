import os
from PIL import Image
import numpy as np
import rembg
import cv2
from skimage.measure import regionprops, label


def read_coordinates(file_path, image_width, image_height):
    """ Читает нормализованные координаты и конвертирует их в пиксельные значения. """
    coordinates = []
    with open(file_path, 'r') as file:
        for line in file:
            values = list(map(float, line.strip().split()))
            if len(values) == 5:
                _, x_center, y_center, width, height = values
                left = int((x_center - width / 2) * image_width)
                top = int((y_center - height / 2) * image_height)
                right = int((x_center + width / 2) * image_width)
                bottom = int((y_center + height / 2) * image_height)
                coordinates.append((left, top, right, bottom))
    return coordinates


def remove_background(image):
    """ Удаляет фон с помощью rembg, сохраняя прозрачность. """
    input_data = np.array(image)
    output_data = rembg.remove(input_data)
    return Image.fromarray(output_data)


def align_symbol(image):
    """ Выравнивает значок, не обрезая его, на основе анализа формы. """
    img_array = np.array(image.convert("RGBA"))

    # Преобразуем изображение в градации серого
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGBA2GRAY)

    # Применяем пороговую обработку
    _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)

    # Находим контуры
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        # Создаём маску
        mask = np.zeros_like(thresh)
        cv2.drawContours(mask, contours, -1, 255, thickness=cv2.FILLED)

        # Используем skimage для определения минимального bounding box
        labeled_mask = label(mask)
        regions = regionprops(labeled_mask)

        if regions:
            minr, minc, maxr, maxc = regions[0].bbox  # Границы объекта

            # Обрезаем изображение по границам значка
            cropped = img_array[minr:maxr, minc:maxc]

            # Определяем угол наклона
            orientation = regions[0].orientation * 180 / np.pi

            # Поворачиваем так, чтобы значок был вертикальным
            rotated = Image.fromarray(cropped)
            rotated = rotated.rotate(-orientation, expand=True, fillcolor=(0, 0, 0, 0))

            return rotated

    return image


class ImageController:
    def __init__(self, image_path, coordinates_path):
        """ Инициализация контроллера изображения. """
        self.image = Image.open(image_path).convert("RGBA")  # RGBA для прозрачности
        self.width, self.height = self.image.size
        self.coordinates = read_coordinates(coordinates_path, self.width, self.height)

    def crop_images(self, remove_bg=False, align=False):
        """ Обрезает изображение по координатам и выполняет доп. обработку. """
        cropped_images = [self.image.crop(coords) for coords in self.coordinates]

        if remove_bg:
            cropped_images = [remove_background(img) for img in cropped_images]

        if align:
            cropped_images = [align_symbol(img) for img in cropped_images]

        return cropped_images

    def save_cropped_images(self, output_folder, remove_bg=False, align=False):
        """ Сохраняет обработанные изображения. """
        os.makedirs(output_folder, exist_ok=True)
        for i, cropped_img in enumerate(self.crop_images(remove_bg, align)):
            output_path = f"{output_folder}/cropped_{i}.png"
            cropped_img.save(output_path, format="PNG")  # Сохраняем прозрачность


# Пример использования
if __name__ == "__main__":
    image_path = "input.jpg"
    coordinates_path = "coordinates.txt"
    output_folder = "output_images"

    remove_bg = True   # Удаление фона
    align = True       # Выровнять значки

    controller = ImageController(image_path, coordinates_path)
    controller.save_cropped_images(output_folder, remove_bg, align)
