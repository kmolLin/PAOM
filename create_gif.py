import imageio
import os
from glob import glob

file = glob("tmp_img/*.jpg")
file.sort(key=os.path.getctime)
print(file)

images = []
for filename in file:
    images.append(imageio.imread(filename))
imageio.mimsave('movie.gif', images)