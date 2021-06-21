#计算laplace算子
import numpy as np 
from scipy.ndimage import variance
from skimage import io
from skimage.color import rgb2gray
from skimage.filters import laplace
from sklearn import preprocessing, svm
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt


def process(img):
    edge_laplace = laplace(img, ksize=3)
    # print(f"Variance: {variance(edge_laplace)}")
    # print(f"Maximum : {np.amax(edge_laplace)}")
    return variance(edge_laplace), np.amax(edge_laplace)


sharp_laplaces = []
blurry_laplaces = []
for i in range(32):
    path = f'C:/Users/smpss/kmol/PAOM/tmp_img/{i}.jpg'
    img = io.imread(path)
    img = rgb2gray(img)
    features = process(img)
    if i < 19:
        blurry_laplaces.append(features)
    else:
        sharp_laplaces.append(features)
# start with the results from the previous script


# set class labels (non-blurry / blurry) and prepare features
y = np.concatenate((np.ones((19, )), np.zeros((13, ))), axis=0)
laplaces = np.concatenate((np.array(blurry_laplaces), np.array(sharp_laplaces)), axis=0)

# scale features
laplaces = preprocessing.scale(laplaces)

kmeans = KMeans(n_clusters=2)
kmeans.fit(laplaces)
new_dy = kmeans.predict(laplaces)


plt.subplot(121)
plt.title('Original data (Hand mark)')
plt.scatter(laplaces.T[0], laplaces.T[1], c=y, cmap=plt.cm.Set1)
# 根據重新分成的 5 組來畫出資料
plt.subplot(122)
plt.title('KMeans=2 groups')
plt.scatter(laplaces.T[0], laplaces.T[1], c=new_dy, cmap=plt.cm.Set1)
plt.show()
print(new_dy)

exit()
for i in range(len(laplaces)):
    if y[i] == 1:
        plt.scatter(laplaces[i][0], laplaces[i][1], c="r")
    else:
        plt.scatter(laplaces[i][0], laplaces[i][1], c="g")


plt.show()


# train the classifier (support vector machine)
clf = svm.SVC(kernel='linear')
clf.fit(laplaces, y)

# print parameters
print(f'Weights: {clf.coef_[0]}')
print(f'Intercept: {clf.intercept_}')

# make sample predictions

# clf.predict([[0.00040431, 0.1602369]])  # result: 0 (blurred)
# clf.predict([[0.00530690, 0.7531759]])  # result: 1 (sharp)

for i in range(3):
    path = f'C:/Users/smpss/kmol/PAOM/tmp_img/{i+22}.jpg'
    img = io.imread(path)
    img = rgb2gray(img)
    features = process(img)

    print(clf.predict([features]))
