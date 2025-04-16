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
        self.worthington = np.zeros(n_frames)
        self.parameters = np.zeros((n_frames, n_params))
        self.contact_angles = np.zeros((n_frames,2))

    def time_IFT_vol_area(self, i):
        # build the time-IFT-volume-area array used in the plotting function
        return [self.time[i], self.gamma_IFT_mN[i], self.volume[i], self.area[i]]

    def export_data(self, input_file, location, filename, i):

        # header and comment not supported for version number < 1.7
        # this is a hack routine to check this...
        # also - this outputs variables into a csv file with 5 significant figures

        out = []
        out.append(str(input_file))
        out.append(self.time[i])
        header = []
        header.append("Filename,")
        header.append("Time (s),")
        for key1 in self.contact_angles.keys():
            for key2 in self.contact_angles[key1].keys():
                if 'angle' in key2:
                    header.append(key1+' '+key2+',')
                    out.append(str(self.contact_angles[key1][key2]))
        string = ''
        for heading in header:
            string = string+heading
        string = string[:-1]
        array = np.array(out)
        array = array.reshape(1, array.shape[0])

        if not location:
            location = './outputs/'

        output_file = location + '/' + filename
        with open(output_file, 'a') as f:
            if i==0:
                f.write(string+'\n')
            #for val in array[0]:
            for val in out:
                f.write(str(val)+',')
            f.write('\n')
        if 0:
            try:
                f = open(output_file,'a')
                np.savetxt(f, self.output_data(input_file,i), delimiter=',', fmt='%10.5f', header=self.header_string(i), comments='')
                f.close()
            except:
                #np.savetxt(f, self.output_data(), delimiter=',', fmt='%10.5f')
                np.savetxt(f, self.output_data(input_file,i), fmt='%10.5f') # was This
