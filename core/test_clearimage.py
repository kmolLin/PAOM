import numpy as np 
import cv2

import matplotlib.pyplot as plt

np.set_printoptions(threshold=np.inf)
def intensity(img):
    print(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))

def gradient(img, kernel_size=5):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    sobelx = cv2.Sobel(img, cv2.CV_8U, 1, 0, ksize=kernel_size)
    sobely = cv2.Sobel(img, cv2.CV_8U, 0, 1, ksize=kernel_size)
    s = np.sqrt(sobelx * sobelx + sobely * sobely)
    T1 = 0.12 * np.max(s)
    T2 = 0.06 * np.max(s)

    # s[s > T1] = 255
    # s = np.where(T1 > s > T2, 0.5)
    # s[T1>= s >= T2] = 0.5
    # s[T2 > s] = 0
    print(s)

    # print(s.shape)
    test = s.astype(img.dtype)
    
    cv2.namedWindow("test1", cv2.WINDOW_NORMAL)
    cv2.imshow("test1", test)
    cv2.waitKey(0)
    
# Load image
path = f'C:/Users/smpss/kmol/PAOM/tmp_img/21.jpg'

img = cv2.imread(path)

# intensity(img)
# gradient(img)
# dst = cv2.Laplacian(img, cv2.CV_8U, ksize=5)
cv2.namedWindow("test", cv2.WINDOW_NORMAL)
cv2.imshow("test", img)
cv2.waitKey(0)
# img = io.imread(path)

import cv2
import numpy as np
from matplotlib import pyplot as plt
#from sklearn import svm, datasets
SZ=20
bin_n = 16 # Number of bins

svm_params = dict( kernel_type = cv2.ml.SVM_LINEAR,
     svm_type = cv2.ml.SVM_C_SVC,
     C=2.67, gamma=5.383 )

affine_flags = cv2.WARP_INVERSE_MAP|cv2.INTER_LINEAR

def deskew(img):
 m = cv2.moments(img)
 if abs(m['mu02']) < 1e-2:
  return img.copy()
 skew = m['mu11']/m['mu02']
 M = np.float32([[1, skew, -0.5*SZ*skew], [0, 1, 0]])
 img = cv2.warpAffine(img,M,(SZ, SZ),flags=affine_flags)
 return img

def hog(img):
 gx = cv2.Sobel(img, cv2.CV_32F, 1, 0)
 gy = cv2.Sobel(img, cv2.CV_32F, 0, 1)
 mag, ang = cv2.cartToPolar(gx, gy)
 bins = np.int32(bin_n*ang/(2*np.pi)) # quantizing binvalues in (0...16)
 bin_cells = bins[:10,:10], bins[10:,:10], bins[:10,10:], bins[10:,10:]
 mag_cells = mag[:10,:10], mag[10:,:10], mag[:10,10:], mag[10:,10:]
 hists = [np.bincount(b.ravel(), m.ravel(), bin_n) for b, m in zip(bin_cells, mag_cells)]
 hist = np.hstack(hists)  # hist is a 64 bit vector
 return hist

img = cv2.imread('digits.png')
gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
#print("gray shape=",gray.shape)
# Now we split the image to 5000 cells, each 20x20 size from 1000x2000[rowsxcols] pixel
#先將gray 1000x2000 [rowsxcols] pixel ,row=1000/50 =50個20pixel 
#再將產生的row 的cols =2000/100 =100個20pixel 
cells = [np.hsplit(row,100) for row in np.vsplit(gray,50)] 
#所以cells 為一50x100 的list 每一物件為20x20 pixel

# First half is trainData, remaining is testData
train_cells = [ i[:50] for i in cells ]  #i=0-49 =50個  total =50x50 =2500 個20x20pixel
test_cells = [ i[50:] for i in cells]    #i=0-49 =50個 total =50x50 =2500 個20x20pixel
#so now train_cells and test_cells =50x50[20x20] list
#transfer to [2500][20x20] list
train = list(sum(train_cells, []))
test = list(sum(test_cells, []))

######    Now training   ########################
deskewed=[0]*2500
hogdata=[0]*2500
for i in range(2500):  
 deskewed[i]=deskew(train[i])
 hogdata[i] =hog(deskewed[i])

traindata= np.array(hogdata).astype(np.float32)
#can not use np.float64 ,must use np.int32
responses = np.int32(np.repeat(np.arange(10),250)[:,np.newaxis])

##=====SVM=====================
#SVM in OpenCV 3.1.0 for Python
# Train the SVM
SVM = cv2.ml.SVM_create()
SVM.setType(cv2.ml.SVM_C_SVC)
SVM.setKernel(cv2.ml.SVM_LINEAR)
#SVM.setDegree(0.0)
#SVM.setGamma(0.0)
#SVM.setCoef0(0.0)
#SVM.setC(0)
#SVM.setNu(0.0)
#SVM.setP(0.0)
#SVM.setClassWeights(None)
SVM.setTermCriteria((cv2.TERM_CRITERIA_COUNT, 100, 1.e-06))
SVM.train(traindata, cv2.ml.ROW_SAMPLE, responses)
#predict
#output = SVM.predict(samples)[1].ravel()
#SVM.save('svm_data.dat')
#SVM.save("svm_data.xml")
#SVM.load("svm_data.xml")
#SVM = cv2.ml.SVM_load('svm_data.xml')
######    Now testing  ########################
#get test data
deskewed=[0]*2500
hogdata=[0]*2500
for i in range(2500):  
 deskewed[i]=deskew(test[i])
 hogdata[i] =hog(deskewed[i])
#========================
testData = np.float32(hogdata).reshape(-1,bin_n*4)
result = SVM.predict(testData)

#######   Check Accuracy   ########################
#if result[1].astype(np.int32)==responses 就是match
mask = result[1].astype(np.int32)==responses
correct = np.count_nonzero(mask)
print("correct =",correct)
print (correct*100.0/len(result[1]))

###### Predict testing 2 ########################
#input image data  20x20 pixel
Input_Numer=[0]*10
img_num =[0]*10
deskewed_r =[0]*10
hogdata_r =[0]*10
img_res =[0]*10
testData_r=[0]*10
result=[0]*10
result_str=[0]*10
Input_Numer[0]="0.jpg"
Input_Numer[1]="1.jpg"
Input_Numer[2]="2.jpg"
Input_Numer[3]="3.jpg"
Input_Numer[4]="4.jpg"
Input_Numer[5]="5.jpg"
Input_Numer[6]="6.jpg"
Input_Numer[7]="7.jpg"
Input_Numer[8]="8.jpg"
Input_Numer[9]="9.jpg"
font = cv2.FONT_HERSHEY_SIMPLEX
for i in range(10):  #input 10 number
 img_num[i] = cv2.imread(Input_Numer[i],0)
 deskewed_r[i]=deskew(img_num[i])
 hogdata_r[i] =hog(deskewed_r[i])
 #white screen
 img_res[i] = np.zeros((64,64,3), np.uint8)
 img_res[i][:,:]=[255,255,255]
 #==predict==
 testData_r[i] = np.float32(hogdata_r[i]).reshape(-1,bin_n*4)
 result[i] = SVM.predict(testData_r[i])
 
 print("result[1][0][0] =",result[i][1][0][0].astype(np.int32)) #change type from float32 to int32
 result_str[i]=str(result[i][1][0][0].astype(np.int32))
 if result[i][1][0][0].astype(np.int32)==i:
  cv2.putText(img_res[i],result_str[i],(15,52), font, 2,(0,255,0),3,cv2.LINE_AA)
 else:
  cv2.putText(img_res[i],result_str[i],(15,52), font, 2,(255,0,0),3,cv2.LINE_AA)
#===drawing result======
Input_Numer_name = ['Input 0', 'Input 1','Input 2', 'Input 3','Input 4',\
     'Input 5','Input 6', 'Input 7','Input8', 'Input9']
     
     
predict_Numer_name =['predict 0', 'predict 1','predict 2', 'predict 3','predict 4', \
     'predict 5','predict6 ', 'predict 7','predict 8', 'predict 9']
    
for i in range(10):
 plt.subplot(2,10,i+1),plt.imshow(img_num[i],cmap = 'gray')
 plt.title(Input_Numer_name[i]), plt.xticks([]), plt.yticks([])
 plt.subplot(2,10,i+11),plt.imshow(img_res[i],cmap = 'gray')
 plt.title(predict_Numer_name[i]), plt.xticks([]), plt.yticks([])

plt.show()

