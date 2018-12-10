#! /usr/bin/env python
# -*- coding: utf-8 -*-
import os
import tempfile
import time
from concurrent.futures import wait, ProcessPoolExecutor

import cv2
import numpy as np
from PIL import Image, ImageDraw


class Video2AsciiVideo(object):

    def __init__(self, src, dst, colorful=False):
        self.src = src
        self.dst = dst
        self.colorful = colorful
        self.tmp_image_dir = os.path.join(tempfile.gettempdir(), 'image')
        self.tmp_ascii_image_dir = os.path.join(tempfile.gettempdir(), 'ascii_image')

        self.fps = None
        self.char_table = list('brick')
        self.scale = 1
        self.step = 7

    def init_tmp_dir(self):
        if not os.path.exists(self.src):
            raise Exception("No such file or directory '{}'".format(self.src))
        if os.path.isdir(self.src):
            raise Exception("Is a directory '{}'".format(self.src))

        self.check_dir(self.tmp_image_dir, self.tmp_ascii_image_dir)
        self.del_files(self.tmp_image_dir, self.tmp_ascii_image_dir)

    def handler(self):
        self.init_tmp_dir()
        self.video2image()
        self.ascii_image2video()

    def video2image(self):
        video = cv2.VideoCapture(self.src)
        futures = []
        if video.isOpened():
            total_num = video.get(7)
            with ProcessPoolExecutor() as executor:
                for num in range(int(total_num) - 1):
                    r, frame = video.read()
                    image_name = '{}.jpg'.format(num)
                    cv2.imwrite(os.path.join(self.tmp_image_dir, image_name), frame)
                    future = executor.submit(self.image2ascii, *[image_name])
                    futures.append(future)
                    print('The %d frame images generated' % num)
            wait(futures)
            self.fps = video.get(cv2.CAP_PROP_FPS)
            video.release()
        else:
            print("Read video failed")

    def image2ascii(self, n):
        # read image
        threshold = 0
        old_img = Image.open(os.path.join(self.tmp_image_dir, n))

        if not self.colorful:
            # colourless threshold, black if less-than, vice versa
            threshold = 150
            img = old_img.convert('L')
        else:
            img = old_img

        pix = img.load()
        width = img.size[0]
        height = img.size[1]

        # create new image
        canvas = np.ndarray((height * self.scale, width * self.scale, 3), np.uint8)
        canvas[:, :, :] = 255
        new_image = Image.fromarray(canvas)
        draw = ImageDraw.Draw(new_image)

        # draw
        pix_count = 0
        table_len = len(self.char_table)
        for y in range(height):
            for x in range(width):
                if x % self.step == 0 and y % self.step == 0:
                    if not self.colorful:
                        gray = pix[x, y]
                        color = (255, 255, 255)
                        if gray < threshold:
                            color = (0, 0, 0)
                    else:
                        color = pix[x, y]
                    draw.text((x * self.scale, y * self.scale), self.char_table[pix_count % table_len], color)
                    pix_count += 1

        # save
        dst = os.path.join(self.tmp_ascii_image_dir, n)
        new_image.save(dst)

    def ascii_image2video(self):
        fourcc = cv2.VideoWriter_fourcc(*"MJPG")
        images = os.listdir(self.tmp_ascii_image_dir)
        im = Image.open(os.path.join(self.tmp_ascii_image_dir, images[0]))
        new_video = cv2.VideoWriter(self.dst, fourcc, self.fps, im.size)
        os.chdir(self.tmp_ascii_image_dir)
        for image in range(1, len(images) + 1):
            frame = cv2.imread(str(image) + '.jpg')
            new_video.write(frame)
        print('Video compound finished')
        new_video.release()

    def del_files(self, *paths):
        for path in paths:
            ls = os.listdir(path)
            for i in ls:
                p = os.path.join(path, i)
                if os.path.isdir(p):
                    self.del_files(p)
                else:
                    os.remove(p)

    def check_dir(self, *paths):
        for path in paths:
            if not os.path.exists(path):
                os.makedirs(path)


if __name__ == '__main__':
    start_time = int(time.time())
    video_src = '/Users/brick/input.mp4'  # source video
    video_dst = '/Users/brick/test.avi'  # destination video
    Video2AsciiVideo(video_src, video_dst).handler()
    end_time = int(time.time())
    print("used time : %d second." % (int(time.time()) - start_time))
