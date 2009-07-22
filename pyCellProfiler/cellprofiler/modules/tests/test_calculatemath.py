'''test_calculatemath.py - Test the CalculateMath module
CellProfiler is distributed under the GNU General Public License.
See the accompanying file LICENSE for details.

Developed by the Broad Institute
Copyright 2003-2009

Please see the AUTHORS file for credits.

Website: http://www.cellprofiler.org
'''
__version__="$Revision$"

import base64
from matplotlib.image import pil_to_array
import numpy as np
import os
import Image as PILImage
import scipy.ndimage
from StringIO import StringIO
import unittest
import zlib

import cellprofiler.pipeline as cpp
import cellprofiler.cpmodule as cpm
import cellprofiler.cpimage as cpi
import cellprofiler.measurements as cpmeas
import cellprofiler.objects as cpo
import cellprofiler.workspace as cpw

import cellprofiler.modules.calculatemath as C

OUTPUT_MEASUREMENTS = "outputmeasurements"
MATH_OUTPUT_MEASUREMENTS = "_".join(("Math",OUTPUT_MEASUREMENTS))
OBJECT = ["object%d"%i for i in range(2)]
class TestCalculateMath(unittest.TestCase):
    def test_01_01_load_matlab(self):
        data = ('eJwBTgSx+01BVExBQiA1LjAgTUFULWZpbGUsIFBsYXRmb3JtOiBQQ1dJTiwg'
                'Q3JlYXRlZCBvbjogRnJpIEp1bCAxNyAxNjoxNzoxNyAyMDA5ICAgICAgICAg'
                'ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAAAUlN'
                'DwAAAMYDAAB4nOxYT2/TMBR3t3ZsIFWDCYljDhw4bCUZTNqRwSbooS1i1SSO'
                'buplRm5cJc7U8sk48pH4CMRZ0iYmm/PHaVo0S9bTc/x+fv/sZ6cNADh9DcCO'
                'T3f9vgXuWivkG7HO+UvEGLYttwWa4FU4/tvvV9DBcETQFSQecsGiReNd+5oO'
                '59PFpx4dewT14SQ+2W99bzJCjju4jgTDz1/xDJFL/BOBZIumfUO32MXUDuVD'
                'fHF0sS5lwrptv/96ufRDQ/ADHz+IjfP5H8ByfjPFb/ux+fthH6IZO7qYQZNp'
                'E8jMG45zKsHZFXA4P3Cw9dF39SbItwR5zncn0EKhH2XyO4I85/ueSRDOFodn'
                'gjznP91A20bk+Eg3gnGOo0twGgmcRjBfhf5V278nyHO+azNku5jNw3GVOGXz'
                'KW8cjIzrpuWhoR++j+Ios/+pIM/5c6rZlGmei7L7sS3gcH5IGSQxZ/KxLxKc'
                'AwGH8xzCciBD42RkVNpXdJ/I5LYTctvgu39Gq9S77nNSlR0RlflzK4G3Bfq0'
                '3jwwSsqt2n9152PddTOvP2V4aXV4wFxP+0zoCJLMOKrO4VXXRVV2RbToPipj'
                'V1CnzhwEc+Ck3YN7cLZw0cXYquV8FPe3fmgk5OuuF3nj+y6n/c2EfBPoHd1Q'
                'kV/rcr7L8LLu26z+uK/eFpWT3f+eC/pzHttjfIvHHiQa5qUieuXW6RfVeVLU'
                'n2XsP/MY9R/s2NwA+0W5Dvg/7D8uob//Jpq7JiTR/yMV98Cq7RfzuHOiRl+Z'
                '//Kes0Xuoef8lEJq5Ks+D1T744mAx/nuxOohWPx9MRj9QCYLIBZ65M0T+y1U'
                'ui9ktGzcRPpm7+H/t/F6WTb+QXG1HOpNNxcn7T1GgzxaAqnEEWmR+00MV/Pv'
                'Omgaw6tKTxlu2vtmGY87NYvgFtW3qB2q8mHd8vwxPuuNsynxuY9WZV9W/FXv'
                't0daLZXVxRcgGSfOU48RbKN/CuND6/zxQf4CAAD//2NjYGDgAGJGBghgReKz'
                'IYnzAbEDVAwkz4JFPReSegEo3yc/McUzNzE9tRhhjgcBc0TRzAHxfVMTi0uL'
                'UsFGeeaVpOYVZ5ZUUmCeZ0pqXklmWmVAUWauY2lJfm5iSWYykeaJoZknhnCf'
                'f1JWanIJkgOJCTdeNPNAfOfEnOTSnMSSVN/Ekgwiw59YcyyQzGHDYg5yvDNB'
                '+UIswuyCghD9BgTcwciA7A5GBkMK7GVl4mFiY8P0PyH9IHfxAHGMzCYZfxlt'
                'mbfSb6UZoO7wYESYQ0y612DArR4GRqp6ALPX4U6p2wdz')
        pipeline = cpp.Pipeline()
        def callback(caller,event):
            self.assertFalse(isinstance(event, cpp.LoadExceptionEvent))
        pipeline.add_listener(callback)
        pipeline.load(StringIO(zlib.decompress(base64.b64decode(data))))
        #
        # 6 modules: last two are CalculateMath
        #        
        # 1) Image: Intensity_TotalIntensity_OrigBlue
        #    Image: Intensity_TotalArea_OrigBlue
        #    Divide
        #    ImgMeas
        # 2) Nuclei: Intensity_IntegratedIntensity_OrigBlue
        #    Nuclei: Intensity_MaxIntensity_OrigBlue
        #    Exponent = 2, multiplier = .5
        #    Divide
        #    ObjectMeas
        #
        self.assertEqual(len(pipeline.modules()), 6)
        module = pipeline.modules()[4]
        self.assertTrue(isinstance(module, C.CalculateMath))
        self.assertEqual(module.output_feature_name.value, "ImgMeas")
        self.assertEqual(module.operation.value, C.O_DIVIDE)
        self.assertEqual(module.operands[0].operand_choice, C.MC_IMAGE)
        self.assertEqual(module.operands[1].operand_choice, C.MC_IMAGE)
        self.assertEqual(module.operands[0].operand_measurement.value,
                         "Intensity_TotalIntensity_OrigBlue")
        self.assertEqual(module.operands[1].operand_measurement.value,
                         "Intensity_TotalArea_OrigBlue")
        
        module = pipeline.modules()[5]
        self.assertTrue(isinstance(module, C.CalculateMath))
        self.assertEqual(module.output_feature_name.value, "ObjectMeas")
        self.assertEqual(module.operation.value, C.O_DIVIDE)
        self.assertEqual(module.operands[0].operand_choice, C.MC_OBJECT)
        self.assertEqual(module.operands[1].operand_choice, C.MC_OBJECT)
        self.assertEqual(module.operands[0].operand_objects, "Nuclei")
        self.assertEqual(module.operands[1].operand_objects, "Nuclei")
        self.assertEqual(module.operands[0].operand_measurement.value,
                         "Intensity_IntegratedIntensity_OrigBlue")
        self.assertEqual(module.operands[1].operand_measurement.value,
                         "Intensity_MaxIntensityEdge_OrigBlue")
        self.assertEqual(module.final_exponent.value, 2)
        self.assertEqual(module.final_multiplicand.value, .5)
    
    def test_01_02_load_v1(self):
        data = ('eJztnN1u2zYUgCnnB806tO52sWG90cUGNFtiyGmyNsGQ2km2xVudGk3Qoii6'
                'jLHpmIMkGhKVxhsK7HKPtUfYY+xyjzBRliyJUSJZlpXIoQDBOjQ/Hp6jQ1LU'
                'D5v1o+f1HXmjosjN+tFqF6tIbqmQdomhbck6XZF3DQQp6shE35KbRJd/slR5'
                'TZGVza319a2qYh8rmyDdJjWa9+yfv1oALNq/d+y95P614MpSYGfyIaIU66fm'
                'ApgHn7vpf9v7K2hgeKKiV1C1kOmr8NIbepccDfqjv5qkY6noAGrBzPZ2YGkn'
                'yDBfdD3Q/buFz5F6iH9HnAletpfoDJuY6C7vls+njvQSyullfvj3K98PEucH'
                'lv4wkM7y7wM//3yE3x4E8pddGesdfIY7FlRlrMHTUS1YeUpMeXOh8ubA3kF9'
                'Iu5pDLfI1X/ROT9tFeFhfWsxfJnj2d5gRjcRNC0DaUinaf344uQ31KaBggJ+'
                'TFOvI3ROV78/h20qa5C2e0n8WgqVUwIHBGTi13HP5xs7ipLovQPCepnctFSK'
                '++ogCz6u3lKIl8BjkMze+RA3b/tZR0nqu8DVl8lVZWVdidC7yPHe5vFL7m9a'
                'vU7cJ+Sj4mMY78ni+yOOZ/IekXVCZctEvh1p7U8bn9PSlzY+Jm2Hl7X/admZ'
                'tb5WjL4vOP8wuaFTpJuYDo6b8NwX2JAyKrcWU+49rlwm1+2rnMMe7KNjdpRs'
                'fP2MK4fJe6gL7S5JdtqbvIcNu9UQYzBT8c7rW6soqbhqBJe2nuNwtZh63gXh'
                '88rkF9S05B9VcgLVifWP66fHGfr3JsbPpHFw3eNh3v5Nc72qVBRnW6m6B4Hy'
                'xLiYrZ22r6vTHBeD88CyKwfGRQT1iwNjkrj5lCuXyf642EIG1hBFRqRfbkK/'
                'vcTVfynolwz0j9vO13Put6Pm47Ps340p+5efL1anbB/fb1WV67+eTzuejTMe'
                'TMs+/vw9ieCmGZ/fThiff8ZwP4Nwe2TyL4+etb5jN3DRduWb5WMmvUaq+pK8'
                '335bX229W/ZSdolqafr2W2V1890f1ZW1D8PMh9gmncTlSLtnad7yZMLz04vh'
                'noLw+WEy8/EbBA3X8esflldZUpPotOemrblpe3Dgp0yzX8/zfs2sc3nH+axz'
                'wp/ZcsKf2XJJ/Klc032uInJ5XzfOOpf3/ZFZ50T/mS2XrP/cuPZ63mSuBq72'
                'Z9TzjKP3RG6r0DTdN0CKZG/e3D642r9R99tfI3zaY69NnbEXhPQ2KqDdNy2O'
                'o+apPxADnRrE0jvFs7f3pc9JHMfS+fe98vSr83IYc2w//3Ki+iviPG/zCyrS'
                'ec6z3wn4ScZ6B/ULaHee4+BtjKtZ52ogmzjIqpyi+E1wghOc4AQnxqsi+E1w'
                't5OrgavjvAzCcc52fx46nBYVyV7BCU5wgpsVbj/ARfXfn4Bw/81kYlEV6+jC'
                'ja0i2S04wQlOcIIrBlcLcJM87yqKvYITnOAEJzjBCW72uH9KPidxnOSWJQXy'
                '/xrQE3X983Ugf9mV20hV+wZh64gZFc1Z7MqsqAR2hqtNVZ7bh43AwlNMTz9G'
                'T43TU7tMjzZcjslRhb0PUyvuIk2O1tHnqpnqxR2kU9wd9A1btUWJBiluVxpu'
                'astOrXupTO95jN4dTu9OjL3DZzjQsCX2pbZn8HCJgtEH3MnPq8LpVy7T34Zq'
                '22LfGtqm9Sq7ntS0pTz1BNcTWIrQE4zrkiuX5x6W7t+/uj0BEG5Hfvv671la'
                'vXPSnCRJF+cXd2N45r+PwcXNuZ8mjdeuH4HL83s239b8/wMM1XyW')
        pipeline = cpp.Pipeline()
        def callback(caller,event):
            self.assertFalse(isinstance(event, cpp.LoadExceptionEvent))
        pipeline.add_listener(callback)
        pipeline.load(StringIO(zlib.decompress(base64.b64decode(data))))
        #
        # 2 CalculateMath modules: 4 & 5
        # 4: ImageMeasurement, multiply
        #    Image - Intensity_MaxIntensity_DNA, multiply by 2, raise to 3
        #    Image - Intensity_MeanIntensity_DNA, multiply by 4, raise to 5
        #    multiply by 6 raise to 7
        # 5: ObjectMeasurement, multiply
        #    Nuclei - AreaShape_Area
        #    Nuclei - AreaShape_Perimeter
        #
        self.assertEqual(len(pipeline.modules()), 6)
        module = pipeline.modules()[4]
        module.output_feature_name = "ImageMeasurement"
        self.assertEqual(module.operands[0].operand_choice,C.MC_IMAGE)
        self.assertEqual(module.operands[1].operand_choice,C.MC_IMAGE)
        self.assertEqual(module.operands[0].operand_measurement, "Intensity_MaxIntensity_DNA")
        self.assertEqual(module.operands[1].operand_measurement, "Intensity_MeanIntensity_DNA")
        self.assertEqual(module.operands[0].multiplicand, 2)
        self.assertEqual(module.operands[0].exponent, 3)
        self.assertEqual(module.operands[1].multiplicand, 4)
        self.assertEqual(module.operands[1].exponent, 5)
        self.assertEqual(module.final_multiplicand, 6)
        self.assertEqual(module.final_exponent, 7)
        module = pipeline.modules()[5]
        self.assertEqual(module.operands[0].operand_choice,C.MC_OBJECT)
        self.assertEqual(module.operands[1].operand_choice,C.MC_OBJECT)
        self.assertEqual(module.operands[0].object, "Nuclei")
        self.assertEqual(module.operands[1].object, "Nuclei")
        self.assertEqual(module.operands[0].operand_measurement, "AreaShape_Area")
        self.assertEqual(module.operands[1].operand_measurement, "AreaShape_Perimeter")
    
    def run_workspace(self, operation, m1_is_image_measurement, m1_data,
                      m2_is_image_measurement, m2_data,
                      setup_fn = None):
        '''Create and run a workspace, returning the measurements
        
        m<n>_is_image_measurement - true for an image measurement, false
                                    for object
        m<n>_data - either a single value or an array
        setup_fn - this gets called with the module before running
        '''
        module = C.CalculateMath()
        module.operation.value = operation
        measurements = cpmeas.Measurements()
        for i, operand, is_image_measurement, data in\
            ((0, module.operands[0], m1_is_image_measurement, m1_data),
             (1, module.operands[1], m2_is_image_measurement, m2_data)):
            measurement = "measurement%d"%i
            if is_image_measurement:
                operand.operand_choice.value = C.MC_IMAGE
                measurements.add_image_measurement(measurement, data)
            else:
                operand.operand_choice.value = C.MC_OBJECT
                operand.operand_objects.value = OBJECT[i]
                measurements.add_measurement(OBJECT[i], measurement, data)
            operand.operand_measurement.value = measurement
        module.output_feature_name.value = OUTPUT_MEASUREMENTS
        if setup_fn is not None:
            setup_fn(module)
        pipeline = cpp.Pipeline()
        image_set_list = cpi.ImageSetList()
        workspace = cpw.Workspace(pipeline,
                                  module,
                                  image_set_list.get_image_set(0),
                                  cpo.ObjectSet(),
                                  measurements,
                                  image_set_list)
        module.run(workspace)
        return measurements
    
    def test_02_01_add_image_image(self):
        measurements = self.run_workspace(C.O_ADD, True, 2, True, 2)
        self.assertTrue(measurements.has_feature(cpmeas.IMAGE, MATH_OUTPUT_MEASUREMENTS))
        for i in range(2):
            self.assertFalse(measurements.has_feature(OBJECT[i], MATH_OUTPUT_MEASUREMENTS))
        data = measurements.get_current_measurement(cpmeas.IMAGE, MATH_OUTPUT_MEASUREMENTS)
        self.assertAlmostEqual(data, 4)
    
    def test_02_02_add_image_object(self):
        '''Add an image measurement to each of several object measurements'''
        measurements = self.run_workspace(C.O_ADD, True, 2, False, np.array([1,4,9]))
        self.assertFalse(measurements.has_feature(cpmeas.IMAGE, MATH_OUTPUT_MEASUREMENTS))
        self.assertTrue(measurements.has_feature(OBJECT[1], MATH_OUTPUT_MEASUREMENTS))
        data = measurements.get_current_measurement(OBJECT[1], MATH_OUTPUT_MEASUREMENTS)
        self.assertTrue(np.all(data == np.array([3,6,11])))
    
    def test_02_03_add_object_image(self):
        '''Add an image measurement to each of several object measurements (reverse)'''
        measurements = self.run_workspace(C.O_ADD, False, np.array([1,4,9]), True, 2)
        self.assertFalse(measurements.has_feature(cpmeas.IMAGE, MATH_OUTPUT_MEASUREMENTS))
        self.assertTrue(measurements.has_feature(OBJECT[0], MATH_OUTPUT_MEASUREMENTS))
        data = measurements.get_current_measurement(OBJECT[0], MATH_OUTPUT_MEASUREMENTS)
        self.assertTrue(np.all(data == np.array([3,6,11])))
    
    def test_02_04_add_premultiply(self):
        def fn(module):
            module.operands[0].multiplicand.value = 2
            module.operands[1].multiplicand.value = 3
        
        measurements = self.run_workspace(C.O_ADD, True, 5, True, 7, fn)
        expected = 2 * 5 + 3 * 7
        data = measurements.get_current_measurement(cpmeas.IMAGE, MATH_OUTPUT_MEASUREMENTS)
        self.assertAlmostEqual(data, expected)

    def test_02_05_add_pre_exponentiate(self):
        def fn(module):
            module.operands[0].exponent.value = 2
            module.operands[1].exponent.value = 3
        
        measurements = self.run_workspace(C.O_ADD, True, 5, True, 7, fn)
        expected = 5 ** 2 + 7 ** 3
        data = measurements.get_current_measurement(cpmeas.IMAGE, MATH_OUTPUT_MEASUREMENTS)
        self.assertAlmostEqual(data, expected)
    
    def test_02_06_add_postmultiply(self):
        def fn(module):
            module.final_multiplicand.value = 3
        measurements = self.run_workspace(C.O_ADD, True, 5, True, 7, fn)
        expected = (5 + 7) * 3
        data = measurements.get_current_measurement(cpmeas.IMAGE, MATH_OUTPUT_MEASUREMENTS)
        self.assertAlmostEqual(data, expected)
        
    def test_02_07_add_postexponentiate(self):
        def fn(module):
            module.final_exponent.value = 3
        measurements = self.run_workspace(C.O_ADD, True, 5, True, 7, fn)
        expected = (5 + 7) ** 3
        data = measurements.get_current_measurement(cpmeas.IMAGE, MATH_OUTPUT_MEASUREMENTS)
        self.assertAlmostEqual(data, expected)
    
    def test_02_08_add_log(self):
        def fn(module):
            module.wants_log.value = True
        measurements = self.run_workspace(C.O_ADD, True, 5, True, 7, fn)
        expected = np.log10(5 + 7)
        data = measurements.get_current_measurement(cpmeas.IMAGE, MATH_OUTPUT_MEASUREMENTS)
        self.assertAlmostEqual(data, expected)
    
    def test_02_09_add_object_object(self):
        measurements = self.run_workspace(C.O_ADD, False, np.array([1,2,3]),
                                          False, np.array([1,4,9]))
        self.assertFalse(measurements.has_feature(cpmeas.IMAGE, MATH_OUTPUT_MEASUREMENTS))
        for i in range(2):
            self.assertTrue(measurements.has_feature(OBJECT[i], MATH_OUTPUT_MEASUREMENTS))
            data = measurements.get_current_measurement(OBJECT[i], MATH_OUTPUT_MEASUREMENTS)
            self.assertTrue(np.all(data == np.array([2,6,12])))
    
    def test_03_01_subtract(self):
        measurements = self.run_workspace(C.O_SUBTRACT, True, 7, True, 5)
        data = measurements.get_current_measurement(cpmeas.IMAGE, MATH_OUTPUT_MEASUREMENTS)
        self.assertAlmostEqual(data, 2)

    def test_04_01_multiply(self):
        measurements = self.run_workspace(C.O_MULTIPLY, True, 7, True, 5)
        data = measurements.get_current_measurement(cpmeas.IMAGE, MATH_OUTPUT_MEASUREMENTS)
        self.assertAlmostEqual(data, 35)
    
    def test_04_01_divide(self):
        measurements = self.run_workspace(C.O_DIVIDE, True, 35, True, 5)
        data = measurements.get_current_measurement(cpmeas.IMAGE, MATH_OUTPUT_MEASUREMENTS)
        self.assertAlmostEqual(data, 7)
    
    def test_05_01_measurement_columns_image(self):
        module = C.CalculateMath()
        module.output_feature_name.value = OUTPUT_MEASUREMENTS
        for operand in module.operands:
            operand.operand_choice.value = C.MC_IMAGE
        columns = module.get_measurement_columns(None)
        self.assertEqual(len(columns),1)
        self.assertEqual(columns[0][0], cpmeas.IMAGE)
        self.assertEqual(columns[0][1], MATH_OUTPUT_MEASUREMENTS)
        self.assertEqual(columns[0][2], cpmeas.COLTYPE_FLOAT)
        self.assertEqual(module.get_categories(None,cpmeas.IMAGE)[0], "Math")
        self.assertEqual(module.get_measurements(None, cpmeas.IMAGE, "Math")[0], 
                         OUTPUT_MEASUREMENTS)

    def test_05_02_measurement_columns_image_object(self):
        module = C.CalculateMath()
        module.output_feature_name.value = OUTPUT_MEASUREMENTS
        module.operands[0].operand_choice.value = C.MC_IMAGE
        module.operands[1].operand_choice.value = C.MC_OBJECT
        module.operands[1].operand_objects.value = OBJECT[1]
        columns = module.get_measurement_columns(None)
        self.assertEqual(len(columns),1)
        self.assertEqual(columns[0][0], OBJECT[1])
        self.assertEqual(columns[0][1], MATH_OUTPUT_MEASUREMENTS)
        self.assertEqual(columns[0][2], cpmeas.COLTYPE_FLOAT)
        self.assertEqual(module.get_categories(None,OBJECT[1])[0], "Math")
        self.assertEqual(module.get_measurements(None, OBJECT[1], "Math")[0], 
                         OUTPUT_MEASUREMENTS)
        self.assertEqual(len(module.get_categories(None,cpmeas.IMAGE)), 0)
    
    def test_05_03_measurement_columns_object_image(self):
        module = C.CalculateMath()
        module.output_feature_name.value = OUTPUT_MEASUREMENTS
        module.operands[0].operand_choice.value = C.MC_OBJECT
        module.operands[1].operand_choice.value = C.MC_IMAGE
        module.operands[0].operand_objects.value = OBJECT[0]
        columns = module.get_measurement_columns(None)
        self.assertEqual(len(columns),1)
        self.assertEqual(columns[0][0], OBJECT[0])
        self.assertEqual(columns[0][1], MATH_OUTPUT_MEASUREMENTS)
        self.assertEqual(columns[0][2], cpmeas.COLTYPE_FLOAT)
        self.assertEqual(module.get_categories(None,OBJECT[0])[0], "Math")
        self.assertEqual(module.get_measurements(None, OBJECT[0], "Math")[0], 
                         OUTPUT_MEASUREMENTS)
        self.assertEqual(len(module.get_categories(None,cpmeas.IMAGE)), 0)

    def test_05_04_measurement_columns_object_object(self):
        module = C.CalculateMath()
        module.output_feature_name.value = OUTPUT_MEASUREMENTS
        module.operands[0].operand_choice.value = C.MC_OBJECT
        module.operands[1].operand_choice.value = C.MC_OBJECT
        module.operands[0].operand_objects.value = OBJECT[0]
        module.operands[1].operand_objects.value = OBJECT[1]
        columns = list(module.get_measurement_columns(None))
        self.assertEqual(len(columns),2)
        if columns[0][0] == OBJECT[1]:
            columns = [columns[1],columns[0]]
        for i in range(2):
            self.assertEqual(columns[i][0], OBJECT[i])
            self.assertEqual(columns[i][1], MATH_OUTPUT_MEASUREMENTS)
            self.assertEqual(columns[i][2], cpmeas.COLTYPE_FLOAT)
            self.assertEqual(module.get_categories(None,OBJECT[i])[0], "Math")
            self.assertEqual(module.get_measurements(None, OBJECT[i],"Math")[0], 
                             OUTPUT_MEASUREMENTS)
        self.assertEqual(len(module.get_categories(None,cpmeas.IMAGE)), 0)
        