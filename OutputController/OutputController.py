import os
import zipfile
from PIL import Image, ImageOps, ImageEnhance
from fpdf import FPDF


class OutputController:
    def __init__(self, images):
        """
        :param images: Список изображений (PIL Image)
        """
        self.images = images

    def apply_filters(self, filter_type):
        """
        Применяет фильтр ко всем изображениям.
        :param filter_type: Тип фильтра (grayscale, invert, contrast, threshold)
        """
        filtered_images = []
        for img in self.images:
            if filter_type == "grayscale":
                img = ImageOps.grayscale(img)
            elif filter_type == "invert":
                img = ImageOps.invert(img.convert("RGB"))
            elif filter_type == "contrast":
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(2.0)  # Увеличение контраста в 2 раза
            elif filter_type == "threshold":
                img = img.convert("L")
                img = img.point(lambda p: 255 if p > 128 else 0, "1")  # Черно-белый порог
            filtered_images.append(img)
        self.images = filtered_images

    def save_zip(self, output_path="output.zip"):
        """
        Сохраняет изображения в ZIP-архив.
        :param output_path: Путь к выходному ZIP-файлу
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with zipfile.ZipFile(output_path, "w") as zipf:
            for i, img in enumerate(self.images):
                img_path = f"image_{i}.png"
                img.save(img_path, format="PNG")
                zipf.write(img_path, arcname=os.path.basename(img_path))
                os.remove(img_path)  # Удаляем временные файлы

    def save_pdf(self, output_path="output.pdf", rows=4, cols=3, margin=10):
        """
        Создаёт PDF с изображениями, вписывая их в сетку А4 без искажений.
        :param output_path: Путь к выходному PDF
        :param rows: Количество строк
        :param cols: Количество столбцов
        :param margin: Отступы между значками
        """
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.add_page()

        page_width, page_height = 210, 297  # Размеры A4 в мм
        available_width = page_width - (cols + 1) * margin
        available_height = page_height - (rows + 1) * margin

        cell_width = available_width / cols
        cell_height = available_height / rows

        for i, img in enumerate(self.images):
            if i % (rows * cols) == 0 and i > 0:
                pdf.add_page()  # Новая страница, если закончилось место

            col = i % cols
            row = (i // cols) % rows

            # Получаем исходные размеры значка
            img_width, img_height = img.size
            img_aspect = img_width / img_height
            cell_aspect = cell_width / cell_height

            # Считаем масштаб по диагонали (вписываем без искажений)
            if img_aspect > cell_aspect:
                new_width = cell_width
                new_height = cell_width / img_aspect
            else:
                new_height = cell_height
                new_width = cell_height * img_aspect

            # Меняем размер значка
            img_resized = img.resize((int(new_width * 3.78), int(new_height * 3.78)), Image.LANCZOS)
            img_resized_path = f"temp_{i}.png"
            img_resized.save(img_resized_path)

            # Вычисляем отступы для центрирования значка
            x = margin + col * (cell_width + margin) + (cell_width - new_width) / 2
            y = margin + row * (cell_height + margin) + (cell_height - new_height) / 2

            pdf.image(img_resized_path, x, y, new_width, new_height)

            os.remove(img_resized_path)  # Удаляем временный файл

        pdf.output(output_path, "F")


# Пример использования
if __name__ == "__main__":
    from glob import glob

    # Загружаем все значки из папки
    image_paths = glob("D:\\PyProjects\\ImageController\\output_images\\*.png")
    images = [Image.open(img) for img in image_paths]

    controller = OutputController(images)

    # Применяем фильтр (если нужно)
    # controller.apply_filters("grayscale")

    # Сохраняем ZIP
    controller.save_zip("output_images/output.zip")

    # Сохраняем PDF с настройкой сетки
    controller.save_pdf("output_images/output.pdf", rows=3, cols=4)
