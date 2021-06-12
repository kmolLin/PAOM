# -*- coding: utf-8 -*-
import cv2
import numpy as np
import os
import math
import time



def resize(image, width=None, height=None, inter=cv2.INTER_AREA):
    # initialize the dimensions of the image to be resized and
    # grab the image size
    dim = None
    (h, w) = image.shape[:2]

    # if both the width and height are None, then return the
    # original image
    if width is None and height is None:
        return image

    # check to see if the width is None
    if width is None:
        # calculate the ratio of the height and construct the
        # dimensions
        r = height / float(h)
        dim = (int(w * r), height)

    # otherwise, the height is None
    else:
        # calculate the ratio of the width and construct the
        # dimensions
        r = width / float(w)
        dim = (width, int(h * r))

    # resize the image
    resized = cv2.resize(image, dim, interpolation=inter)

    # return the resized image
    return resized


def pyramid(image, scale=1.5, minSize=(30, 30)):
    # yield the original image
    yield image
    # keep looping over the pyramid
    while True:
        # compute the new dimensions of the image and resize it
        w = int(image.shape[1] / scale)
        image = resize(image, width=w)
        # if the resized image does not meet the supplied minimum
        # size, then stop constructing the pyramid
        if image.shape[0] < minSize[1] or image.shape[1] < minSize[0]:
            break
        # yield the next image in the pyramid
        yield image


def sliding_window(image, stepSize, windowSize):
    # slide a window across the image
    for y in range(0, image.shape[0], stepSize):
        for x in range(0, image.shape[1], stepSize):
            # yield the current window
            yield x, y, image[y:y + windowSize[1], x:x + windowSize[0]]


def runcode(png_file, original_image):
    gray = cv2.imread(png_file, 0)

    original_image = cv2.imread(original_image, 0)
    # sift = cv2.xfeatures2d.SIFT_create()
    orb = cv2.ORB_create()
    kp1, des1 = orb.detectAndCompute(gray, None)
    kp2, des2 = orb.detectAndCompute(original_image, None)

    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)
    # flann = cv2.FlannBasedMatcher(index_params, search_params)
    # matches = flann.knnMatch(des1, des2, k=2)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)
    print(matches)
    matches = sorted(matches, key=lambda x: x.distance)
    good = []
    for i in range(len(matches)):
        if matches[i].distance < 0.75 * matches[-1].distance:
            good.append(matches[i])

    MIN_MATCH_COUNT = 7
    te = 0
    if len(good) > MIN_MATCH_COUNT:
        te = 1
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

        theta = -math.atan2(M[0, 1], M[0, 0]) * 180 / math.pi
        matchesMask = mask.ravel().tolist()
        h, w = gray.shape
        pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
        dst = cv2.perspectiveTransform(pts, M)
        # cv2.polylines(original_image_color, [np.int32(dst)], True, 255, 3, cv2.LINE_AA)
    else:
        print("Not enough matches are found - {}/{}".format(len(good), MIN_MATCH_COUNT))
        matchesMask = None

    if te == 1:
        return dst, theta
    else:
        return None, None


if __name__ == "__main__":

    image = cv2.imread("tmp_img/test/50.jpeg")
    (winW, winH) = (128 * 4, 128 * 4)
    old = time.time()
    for resized in pyramid(image, scale=1.5):
        # loop over the sliding window for each layer of the pyramid
        for (x, y, window) in sliding_window(resized, stepSize=128, windowSize=(winW, winH)):
            # if the window does not meet our desired window size, ignore it
            if window.shape[0] != winH or window.shape[1] != winW:
                continue
            # THIS IS WHERE YOU WOULD PROCESS YOUR WINDOW, SUCH AS APPLYING A
            # MACHINE LEARNING CLASSIFIER TO CLASSIFY THE CONTENTS OF THE
            # WINDOW
            # since we do not have a classifier, we'll just draw the window
            clone = resized.copy()
            cv2.rectangle(clone, (x, y), (x + winW, y + winH), (0, 255, 0), 2)
            crop_area = resized[y: y + winH, x:x + winW]
            cv2.namedWindow("Window", cv2.WINDOW_NORMAL)
            cv2.namedWindow("crop Area", cv2.WINDOW_NORMAL)
            cv2.imshow("Window", clone)
            cv2.imshow("crop Area", crop_area)
            cv2.waitKey(1)
            time.sleep(0.025)
    # print(time.time() - old)
    # for i in range(300):
    #     dst, theta = runcode("tmp.jpeg", f"tmp_img/test/{i}.jpeg")
    #     if dst is None:
    #         continue
    #     original_image_color = cv2.imread(f"tmp_img/test/{i}.jpeg")
    #     cv2.polylines(original_image_color, [np.int32(dst)], True, 255, 3, cv2.LINE_AA)
    #     cv2.namedWindow("test", cv2.WINDOW_NORMAL)
    #     cv2.imshow("test", original_image_color)
    #     cv2.waitKey(0)
    # print(dst)

exit()
box = cv2.imread("tmp.jpeg")
box_in_sence = cv2.imread("tmp_img/test/50.jpeg")
# cv2.imshow("box", box)
# cv2.imshow("box_in_sence", box_in_sence)

# Create ORB Feature Extractor
orb = cv2.ORB_create()
kp1, des1 = orb.detectAndCompute(box, None)
kp2, des2 = orb.detectAndCompute(box_in_sence, None)

# matching
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
matches = bf.match(des1, des2)
goodMatches = []

# good features
matches = sorted(matches, key=lambda x: x.distance)
for i in range(len(matches)):
    if matches[i].distance < 0.75 * matches[-1].distance:
        goodMatches.append(matches[i])

result = cv2.drawMatches(box, kp1, box_in_sence, kp2, goodMatches, None)

obj_pts, scene_pts = [], []

# save obj and scene good locate
for f in goodMatches:
    obj_pts.append(kp1[f.queryIdx].pt)
    scene_pts.append(kp2[f.trainIdx].pt)

# H, _= cv2.findHomography(np.float32(obj_pts), np.float32(scene_pts), cv2.RANSAC)

M, mask = cv2.findHomography(np.float32(obj_pts), np.float32(scene_pts), cv2.RANSAC, 5.0)
print(M)
h, w = box.shape[0:2]

pts = np.float32([[0, 0], [0, h], [w, h], [w, 0]]).reshape(-1, 1, 2)
dst = cv2.perspectiveTransform(pts, M).reshape(-1, 2)
print(dst)
# add offset
for i in range(4):
    dst[i][0] += w

cv2.polylines(result, [np.int32(dst)], True, (0, 255, 0), 3, cv2.LINE_AA)
cv2.namedWindow("test", cv2.WINDOW_NORMAL)
cv2.imshow("test", result)
cv2.waitKey(0)
# cv2.imshow("orb-match", result)
# cv2.imwrite("orv-match.jpg", result)
#
# cv2.waitKey(0)
# cv2.destroyAllWindows()
