#!/usr/bin/env python
# coding=utf-8
import numpy as np

class ExtractedData(object):
    def __init__(self, n_frames, n_params):
        self.initial_image_time = None
        self.time = np.zeros(n_frames)
        self.gamma_IFT_mN = np.zeros(n_frames)
        self.pixels_to_mm = np.zeros(n_frames)
        self.volume = np.zeros(n_frames)
        self.area = np.zeros(n_frames)
        self.parameters = np.zeros((n_frames, n_params))

    def time_IFT_vol_area(self, i):
        # build the time-IFT-volume-area array used in the plotting function
        return [self.time[i], self.gamma_IFT_mN[i], self.volume[i], self.area[i]]
   
    def output_data(self):
        # builds the output array
        array = np.concatenate((np.array([self.time, self.gamma_IFT_mN, self.volume, self.area]).T, self.parameters), axis=1)
        return array

    def header_string(self):
        return "Time (s),IFT (mN/m),Volume (uL),Area (mm2),x-apex (px),y-apex (px),Apex radius (px),Bond number,Rotation (degree)"

    def export_data(self, filename):
        # header and comment not supported for version number < 1.7
        # this is a hack routine to check this...
        # also - this outputs variables into a csv file with 5 significant figures
        try:
            np.savetxt(filename, self.output_data(), delimiter=',', fmt='%10.5f', header=self.header_string(), comments='')
        except:
            with open(filename, 'w') as f:
                f.write(self.header_string()+'\n')
                np.savetxt(f, self.output_data(), delimiter=',', fmt='%10.5f')
