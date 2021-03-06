"""Image Processing"""
import cv2
import numpy as np


def edge_detection(img, debug_mode=True, save_name='images/edge.png'):
    """Canny edge detection"""
    edge_img = cv2.Canny(img, 50, 75)
    if debug_mode:
        cv2.imwrite(save_name, edge_img)
    return edge_img


def find_edge(edge_img, left, right, top=0.20, bottom=0.70):
    """
    Get all positions of white pixel
    to reduce the amount of computation
    """
    height = edge_img.shape[0]
    width = edge_img.shape[1]
    edge_positions = np.nonzero(edge_img[int(height * top):int(height * bottom), int(width * left):int(width * right)])
    return edge_positions[0] + int(height * top), edge_positions[1] + int(width * left)


def multiscale_search(screen, avatar, scale=0.3, step=0.1):
    h, w = avatar.shape
    H, W = screen.shape
    best_match = None
    for s in np.arange(1 - scale, 1 + scale, step):
        resized_screen = cv2.resize(screen, (int(W * s), int(H * s)))
        res = cv2.matchTemplate(resized_screen, avatar, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= res.max())
        pos_h, pos_w = loc[0][0], loc[1][0]
        if best_match is None or res[pos_h][pos_w] > best_match[-1]:
            best_match = (pos_h, pos_w, s, res[pos_h][pos_w])
    if best_match is None:
        return 0, 0, 0, 0
    pos_h, pos_w, s, _ = best_match
    h_top, x_left = int(pos_h / s), int(pos_w / s)
    h_bottom, x_right = int((pos_h + h) / s), int((pos_w + w) / s)
    return h_top, x_left, h_bottom, x_right


def find_avatar(img, avatar_img, scale):
    """find position of the avatar"""
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h_top, x_left, h_bottom, x_right = multiscale_search(img, avatar_img, scale=scale)
    h_center, w_center = int((h_top + 13 * h_bottom) / 14.), (x_left + x_right) // 2
    # get the height of avatar
    if h_center == 0:
        print("Please confirm whether the screen is the game interface. ")
        return False
    return (h_center, w_center), (h_top, x_left), (h_bottom, x_right)


def find_platform(img, edge_img, left=0, right=0):
    """find position of the platform"""
    if not right:
        right = img.shape[1]
    height = img.shape[0]
    width = img.shape[1]
    # Get the range size
    edge_right = 0
    broadband_max = (0, 0, 0)
    platform_bgr = (-1, -1, -1)
    tmp_h = -1
    level = 0
    edge_positions = find_edge(edge_img, left=left / width, right=right / width, bottom=0.50)
    if edge_positions:
        for h, x in zip(*edge_positions):
            if level > height * 0.06:
                find_platform_spare(edge_positions)
                level += 1
                if platform_bgr[0] == -1 \
                        and (img[h][x] == img[h + 1][x]).all() \
                        and (img[h][x] == img[h + 2][x]).all() \
                        and (img[h][x] == img[h + 3][x]).all():
                    # find the color of the platform
                    platform_bgr = img[h][x]
                    break
        for h, x in zip(*edge_positions):
            pixel = img[h][x]
            if pixel[0] in range(platform_bgr[0] - 2, platform_bgr[0] + 2) \
                    and pixel[1] in range(platform_bgr[1] - 2, platform_bgr[1] + 2) \
                    and pixel[2] in range(platform_bgr[2] - 2, platform_bgr[2] + 2):
                if h > tmp_h:
                    tmp_h = h
                    edge_left = (h, x)
                    if edge_right and edge_right[1] - edge_left[1] > broadband_max[2]:
                        broadband_max = (edge_right[0], edge_left[1], edge_right[1] - edge_left[1])
                else:
                    edge_right = (h, x)
    # find the center of platform
    platform_position = (broadband_max[0], broadband_max[1] + (broadband_max[2] + 1) // 2)
    if broadband_max[0] == 0 or broadband_max[1] + (broadband_max[2] + 1) // 2 == 0:
        platform_position = find_platform_spare(edge_positions)
    return platform_position


def find_platform_spare(edge_positions):
    broadband_max = (0, 0, 0)
    edge_right = 0
    tmp_h = -1
    if edge_positions:
        for h, x in zip(*edge_positions):
            if h > tmp_h:
                tmp_h = h
                edge_left = (h, x)
                if edge_right and edge_right[1] - edge_left[1] > broadband_max[2]:
                    broadband_max = (edge_right[0], edge_left[1], edge_right[1] - edge_left[1])
                elif edge_right and edge_right[1] - edge_left[1] <= broadband_max[2]:
                    break
            else:
                edge_right = (h, x)
    # find the center of platform
    platform_position = (broadband_max[0], broadband_max[1] + (broadband_max[2] + 1) // 2)
    return platform_position


def img_cropped(left=0, right=0):
    """cropped image into 2 parts (score and platform part)"""
    if not right:
        right = cv2.imread('screen.png').shape[1]
    img = cv2.imread('screen.png')
    height = img.shape[0]
    width = img.shape[1]
    # Get the picture size
    cropped_score = img[height // 11: height // 6, 0: width // 2]  # Get score screenshot
    cropped_pltform = img[height // 6: height * 2 // 3, left: right]
    cv2.imwrite('score.png', cropped_score)
    cv2.imwrite('pltform.png', cropped_pltform)
