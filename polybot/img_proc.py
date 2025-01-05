from pathlib import Path
from matplotlib.image import imread, imsave
from random import random


def rgb2gray(rgb):
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
    return gray


class Img:

    def __init__(self, path):
        """
        Do not change the constructor implementation
        """
        self.path = Path(path)
        self.data = rgb2gray(imread(path)).tolist()

    def save_img(self):
        """
        Do not change the below implementation
        """
        new_path = self.path.with_name(self.path.stem + '_filtered' + self.path.suffix)
        imsave(new_path, self.data, cmap='gray')
        return new_path

    def blur(self, blur_level=16):

        height = len(self.data)
        width = len(self.data[0])
        filter_sum = blur_level ** 2

        result = []
        for i in range(height - blur_level + 1):
            row_result = []
            for j in range(width - blur_level + 1):
                sub_matrix = [row[j:j + blur_level] for row in self.data[i:i + blur_level]]
                average = sum(sum(sub_row) for sub_row in sub_matrix) // filter_sum
                row_result.append(average)
            result.append(row_result)

        self.data = result

    def contour(self):
        for i, row in enumerate(self.data):
            res = []
            for j in range(1, len(row)):
                res.append(abs(row[j - 1] - row[j]))

            self.data[i] = res

    def rotate(self, num_rotations=1):
        """
        Rotates the image clockwise.
        """
        for rotation_number in range(num_rotations):
            # Initialize a list, which is rotated in comparison to the original data list
            template_lst = [[row_index for row_index in range(len(self.data))] for col_index in
                            range(len(self.data[0]))]
            # Initialize a temp image, with its data set to the newly created template_lst
            temp_img = Img(self.path)
            temp_img.data = template_lst
            # Perform image rotation
            for row_index in range(len(self.data)):
                for col_index in range(len(self.data[row_index])):
                    # Iterate over this image's pixels and rotate them, creating a temporary rotated image
                    temp_img.data[col_index][len(self.data) - 1 - row_index] = self.data[row_index][col_index]
            self.data = temp_img.data

    def salt_n_pepper(self):
        """
        Randomly applies image distortion, coloring some image pixels white or black (self and pepper respectively).
        """
        for row_index in range(len(self.data)):
            for col_index in range(len(self.data[row_index])):
                rnd_float = random()
                if rnd_float < 0.2:
                    # Add salt to this pixel
                    self.data[row_index][col_index] = 255
                elif rnd_float > 0.8:
                    # Add pepper to this pixel
                    self.data[row_index][col_index] = 0

    def concat(self, other_img, direction='horizontal'):
        """
        Concatenates self with other_img so other_img is drawn next to self.
        direction parameter changes the direction of concatenation and can either be 'horizontal' or 'vertical'.
        """
        if direction == 'horizontal':
            if len(self.data) != len(other_img.data):
                # If number of rows is different, then the pictures have different heights
                raise RuntimeError("Pictures with different heights cannot be horizontally concatenated")
            # Horizontally concatenate images
            for row_index in range(len(self.data)):
                self.data[row_index] += other_img.data[row_index]
        elif direction == 'vertical':
            if len(self.data[0]) != len(other_img.data[0]):
                # If number of columns is different, then the pictures have different widths
                raise RuntimeError("Pictures with different widths cannot be vertically concatenated")
            # Vertically concatenate images
            for row_index in range(len(self.data[0])):
                self.data.append(other_img.data[row_index])

    def segment(self):
        """
        Segments the image into black and white pixels according to pixel intensity.
        """
        temp_img = Img(self.path)
        for row_index in range(len(self.data)):
            for col_index in range(len(self.data[row_index])):
                # Iterate over this image's pixels and converts the values to black (0) or white (255) based on
                # intensity threshold.
                if self.data[row_index][col_index] > 100:
                    self.data[row_index][col_index] = 255
                else:
                    self.data[row_index][col_index] = 0