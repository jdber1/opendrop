import basic_extract_data
import numpy as np


class SessileExtractData(basic_extract_data.BasicExtractedData):
    def output_data(self, i):
        # builds the output array
        array = np.concatenate((np.array(
            [self.time[i], self.gamma_IFT_mN[i], self.volume[i], self.area[i], -self.worthington[i]]), self.parameters[i]))
        array = array.reshape(1, array.shape[0])
        return array
