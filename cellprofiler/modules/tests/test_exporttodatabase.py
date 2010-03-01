'''test_exporttodatabase.py - test the ExportToDatabase module

CellProfiler is distributed under the GNU General Public License.
See the accompanying file LICENSE for details.

Developed by the Broad Institute
Copyright 2003-2010

Please see the AUTHORS file for credits.

Website: http://www.cellprofiler.org
'''

__version__="$Revision$"

import base64
import numpy as np
import os
import Image as PILImage
import scipy.ndimage
from StringIO import StringIO
import tempfile
import unittest
import uuid
import zlib

from cellprofiler.preferences import set_headless
set_headless()

import cellprofiler.cpmodule as cpm
import cellprofiler.pipeline as cpp
import cellprofiler.settings as cps
import cellprofiler.cpimage as cpi
import cellprofiler.workspace as cpw
import cellprofiler.objects as cpo
import cellprofiler.measurements as cpmeas

import cellprofiler.modules.exporttodatabase as E
import cellprofiler.modules.identify as I

M_CATEGORY = "my"
OBJ_FEATURE = 'objmeasurement'
INT_IMG_FEATURE = 'int_imagemeasurement'
FLOAT_IMG_FEATURE = 'float_imagemeasurement'
STRING_IMG_FEATURE = 'string_imagemeasurement'
LONG_IMG_FEATURE = 'image_measurement_with_a_column_name_that_exceeds_64_characters_in_width'
LONG_OBJ_FEATURE = 'obj_measurement_with_a_column_name_that_exceeds_64_characters_in_width'
WIERD_IMG_FEATURE = 'image_measurement_with_"!@%*\n~!\t\ra\+=''and other &*^% in it..........'
WIERD_OBJ_FEATURE = 'measurement w/"!@%*\n~!\t\ra\+=''and other &*^% in it'
OBJ_MEASUREMENT, INT_IMG_MEASUREMENT, FLOAT_IMG_MEASUREMENT, \
    STRING_IMG_MEASUREMENT, LONG_IMG_MEASUREMENT, LONG_OBJ_MEASUREMENT, \
    WIERD_IMG_MEASUREMENT, WIERD_OBJ_MEASUREMENT = \
    ['_'.join((M_CATEGORY, x))
     for x in (OBJ_FEATURE, INT_IMG_FEATURE, FLOAT_IMG_FEATURE, 
               STRING_IMG_FEATURE, LONG_IMG_FEATURE, LONG_OBJ_FEATURE,
               WIERD_IMG_FEATURE, WIERD_OBJ_FEATURE)]
OBJECT_NAME = 'myobject'
IMAGE_NAME = 'myimage'
OBJECT_COUNT_MEASUREMENT = 'Count_%s'%OBJECT_NAME

ALTOBJECT_NAME = 'altobject'
ALTOBJECT_COUNT_MEASUREMENT = 'Count_%s'%ALTOBJECT_NAME

INT_VALUE = 10
FLOAT_VALUE = 15.5
STRING_VALUE = "Hello, world"
OBJ_VALUE = np.array([1.5, 3.67, 2.8])
PLATE = "P-12345"
WELL = "A01"

class TestExportToDatabase(unittest.TestCase):
    def setUp(self):
        self.__cursor = None
    
    @property
    def cursor(self):
        if self.__cursor is None:
            import MySQLdb
            from MySQLdb.cursors import SSCursor
            connection = MySQLdb.connect(host='imgdb01',
                                         user='cpuser',
                                         passwd='cPus3r')
            self.__cursor = SSCursor(connection)
        return self.__cursor
    
    def get_sqlite_cursor(self, module):
        from pysqlite2 import dbapi2 as sqlite
        self.assertTrue(isinstance( module, E.ExportToDatabase))
        file_name = os.path.join(module.output_directory.value,
                                 module.sqlite_file.value)
        connection = sqlite.connect(file_name)
        cursor = connection.cursor()
        return cursor, connection
    
    def test_01_00_01_load_matlab_4(self):
        data=r"""CellProfiler Pipeline: http://www.cellprofiler.org
Version:1
SVNRevision:8925
FromMatlab:True

ExportToDatabase:[module_num:1|svn_version:\'8913\'|variable_revision_number:4|show_window:False|notes:\x5B\x5D]
    What type of database do you want to use?:MySQL
    For MySQL only, what is the name of the database to use?:MyDatabase
    What prefix should be used to name the SQL Tables in the database (should be unique per experiment)?:ExptTbl_
    What prefix should be used to name the SQL files?:SQLFile_
    Enter the directory where the SQL files are to be saved.  Type period (.) to use the default output folder.:.
"""
        pipeline = cpp.Pipeline()
        def callback(caller, event):
            self.assertFalse(isinstance(event, cpp.LoadExceptionEvent))
        pipeline.add_listener(callback)
        pipeline.load(StringIO(data))
        self.assertEqual(len(pipeline.modules()), 1)
        module = pipeline.modules()[0]
        self.assertTrue(isinstance(module, E.ExportToDatabase))
        self.assertEqual(module.directory_choice, E.DIR_DEFAULT_OUTPUT)
        self.assertTrue(module.want_table_prefix)
        self.assertEqual(module.table_prefix, "ExptTbl_")
        self.assertEqual(module.sql_file_prefix, "SQLFile_")
        self.assertEqual(module.db_name, "MyDatabase")
        self.assertEqual(module.db_type, E.DB_MYSQL)
    
    def test_01_00_02_load_matlab_5(self):
        data=r"""CellProfiler Pipeline: http://www.cellprofiler.org
Version:1
SVNRevision:8925
FromMatlab:True

ExportToDatabase:[module_num:1|svn_version:\'8913\'|variable_revision_number:5|show_window:False|notes:\x5B\x5D]
    What type of database do you want to use?:MySQL
    For MySQL only, what is the name of the database to use?:MyDatabase
    What prefix should be used to name the SQL Tables in the database (should be unique per experiment)?:ExptTbl_
    What prefix should be used to name the SQL files?:SQLFile_
    Enter the directory where the SQL files are to be saved.  Type period (.) to use the default output folder.:.
    Do you want to create a CellProfiler Analyst properties file?:Yes
"""
        pipeline = cpp.Pipeline()
        def callback(caller, event):
            self.assertFalse(isinstance(event, cpp.LoadExceptionEvent))
        pipeline.add_listener(callback)
        pipeline.load(StringIO(data))
        self.assertEqual(len(pipeline.modules()), 1)
        module = pipeline.modules()[0]
        self.assertTrue(isinstance(module, E.ExportToDatabase))
        self.assertEqual(module.directory_choice, E.DIR_DEFAULT_OUTPUT)
        self.assertTrue(module.want_table_prefix)
        self.assertEqual(module.table_prefix, "ExptTbl_")
        self.assertEqual(module.sql_file_prefix, "SQLFile_")
        self.assertEqual(module.db_name, "MyDatabase")
        self.assertEqual(module.db_type, E.DB_MYSQL)
        self.assertTrue(module.save_cpa_properties)
    
    def test_01_00_03_load_matlab_6(self):
        data=r"""CellProfiler Pipeline: http://www.cellprofiler.org
Version:1
SVNRevision:8925
FromMatlab:True

ExportToDatabase:[module_num:1|svn_version:\'8913\'|variable_revision_number:6|show_window:False|notes:\x5B\x5D]
    What type of database do you want to use?:MySQL
    For MySQL only, what is the name of the database to use?:MyDatabase
    What prefix should be used to name the SQL Tables in the database (should be unique per experiment)?:ExptTbl_
    What prefix should be used to name the SQL files?:SQLFile_
    Enter the directory where the SQL files are to be saved.  Type period (.) to use the default output folder.:.
    Do you want to create a CellProfiler Analyst properties file?:Yes - V2.0 format
"""
        pipeline = cpp.Pipeline()
        def callback(caller, event):
            self.assertFalse(isinstance(event, cpp.LoadExceptionEvent))
        pipeline.add_listener(callback)
        pipeline.load(StringIO(data))
        self.assertEqual(len(pipeline.modules()), 1)
        module = pipeline.modules()[0]
        self.assertTrue(isinstance(module, E.ExportToDatabase))
        self.assertEqual(module.directory_choice, E.DIR_DEFAULT_OUTPUT)
        self.assertTrue(module.want_table_prefix)
        self.assertEqual(module.table_prefix, "ExptTbl_")
        self.assertEqual(module.sql_file_prefix, "SQLFile_")
        self.assertEqual(module.db_name, "MyDatabase")
        self.assertEqual(module.db_type, E.DB_MYSQL)
        self.assertTrue(module.save_cpa_properties)
    
    def test_01_00_04_load_matlab_7(self):
        data=r"""CellProfiler Pipeline: http://www.cellprofiler.org
Version:1
SVNRevision:8925
FromMatlab:True

ExportToDatabase:[module_num:1|svn_version:\'8913\'|variable_revision_number:7|show_window:False|notes:\x5B\x5D]
    What type of database do you want to use?:MySQL
    For MySQL only, what is the name of the database to use?:MyDatabase
    What prefix should be used to name the SQL Tables in the database (should be unique per experiment)?:ExptTbl_
    What prefix should be used to name the SQL files?:SQLFile_
    Enter the directory where the SQL files are to be saved.  Type period (.) to use the default output folder.:.
    Which per-image statistics do you want to be calculated?  Select "Do not use" to omit.:Standard deviation
    :Median
    :Do not use
    Do you want to create a CellProfiler Analyst properties file?:Yes - V2.0 format
"""
        pipeline = cpp.Pipeline()
        def callback(caller, event):
            self.assertFalse(isinstance(event, cpp.LoadExceptionEvent))
        pipeline.add_listener(callback)
        pipeline.load(StringIO(data))
        self.assertEqual(len(pipeline.modules()), 1)
        module = pipeline.modules()[0]
        self.assertTrue(isinstance(module, E.ExportToDatabase))
        self.assertEqual(module.directory_choice, E.DIR_DEFAULT_OUTPUT)
        self.assertTrue(module.want_table_prefix)
        self.assertEqual(module.table_prefix, "ExptTbl_")
        self.assertEqual(module.sql_file_prefix, "SQLFile_")
        self.assertEqual(module.db_name, "MyDatabase")
        self.assertEqual(module.db_type, E.DB_MYSQL_CSV)
        self.assertTrue(module.save_cpa_properties)
        self.assertFalse(module.wants_agg_mean)
        self.assertTrue(module.wants_agg_std_dev)
        self.assertTrue(module.wants_agg_median)
    
    def test_01_00_05_load_matlab_8(self):
        data=r"""CellProfiler Pipeline: http://www.cellprofiler.org
Version:1
SVNRevision:8925
FromMatlab:True

ExportToDatabase:[module_num:1|svn_version:\'8913\'|variable_revision_number:8|show_window:False|notes:\x5B\x5D]
    What type of database do you want to use?:MySQL
    For MySQL only, what is the name of the database to use?:MyDatabase
    What prefix should be used to name the SQL Tables in the database (should be unique per experiment)?:ExptTbl_
    What prefix should be used to name the SQL files?:SQLFile_
    Enter the directory where the SQL files are to be saved.  Type period (.) to use the default output folder.:.
    Which per-image statistics do you want to be calculated?  Select "Do not use" to omit.:Standard deviation
    :Median
    :Do not use
    Which objects do you want to export?:Image
    :MyObjects
    :Do not use
    :Do not use
    Do you want to create a CellProfiler Analyst properties file?:Yes - V2.0 format
"""
        pipeline = cpp.Pipeline()
        def callback(caller, event):
            self.assertFalse(isinstance(event, cpp.LoadExceptionEvent))
        pipeline.add_listener(callback)
        pipeline.load(StringIO(data))
        self.assertEqual(len(pipeline.modules()), 1)
        module = pipeline.modules()[0]
        self.assertTrue(isinstance(module, E.ExportToDatabase))
        self.assertEqual(module.directory_choice, E.DIR_DEFAULT_OUTPUT)
        self.assertTrue(module.want_table_prefix)
        self.assertEqual(module.table_prefix, "ExptTbl_")
        self.assertEqual(module.sql_file_prefix, "SQLFile_")
        self.assertEqual(module.db_name, "MyDatabase")
        self.assertEqual(module.db_type, E.DB_MYSQL_CSV)
        self.assertTrue(module.save_cpa_properties)
        self.assertFalse(module.wants_agg_mean)
        self.assertTrue(module.wants_agg_std_dev)
        self.assertTrue(module.wants_agg_median)
        self.assertEqual(module.objects_choice, E.O_SELECT)
        self.assertEqual(module.objects_list.value, "MyObjects")
        
    def test_01_00_06_load_matlab_9(self):
        data=r"""CellProfiler Pipeline: http://www.cellprofiler.org
Version:1
SVNRevision:8925
FromMatlab:True

ExportToDatabase:[module_num:1|svn_version:\'8913\'|variable_revision_number:9|show_window:False|notes:\x5B\x5D]
    What type of database do you want to use?:MySQL
    For MySQL only, what is the name of the database to use?:MyDatabase
    What prefix should be used to name the SQL Tables in the database (should be unique per experiment)?:ExptTbl_
    What prefix should be used to name the SQL files?:SQLFile_
    Enter the directory where the SQL files are to be saved.  Type period (.) to use the default output folder.:.
    Which per-image statistics do you want to be calculated?  Select "Do not use" to omit.:Standard deviation
    :Median
    :Do not use
    Which objects do you want to export?:Image
    :MyObjects
    :MyOtherObjects
    :Do not use
    :Do not use
    :Do not use
    :Do not use
    Do you want to create a CellProfiler Analyst properties file?:Yes - V2.0 format
"""
        pipeline = cpp.Pipeline()
        def callback(caller, event):
            self.assertFalse(isinstance(event, cpp.LoadExceptionEvent))
        pipeline.add_listener(callback)
        pipeline.load(StringIO(data))
        self.assertEqual(len(pipeline.modules()), 1)
        module = pipeline.modules()[0]
        self.assertTrue(isinstance(module, E.ExportToDatabase))
        self.assertEqual(module.directory_choice, E.DIR_DEFAULT_OUTPUT)
        self.assertTrue(module.want_table_prefix)
        self.assertEqual(module.table_prefix, "ExptTbl_")
        self.assertEqual(module.sql_file_prefix, "SQLFile_")
        self.assertEqual(module.db_name, "MyDatabase")
        self.assertEqual(module.db_type, E.DB_MYSQL_CSV)
        self.assertTrue(module.save_cpa_properties)
        self.assertFalse(module.wants_agg_mean)
        self.assertTrue(module.wants_agg_std_dev)
        self.assertTrue(module.wants_agg_median)
        self.assertEqual(module.objects_choice, E.O_SELECT)
        self.assertEqual(module.objects_list.value, "MyObjects,MyOtherObjects")
    
    def test_01_01_load_matlab_10(self):
        data = ('eJwBNATL+01BVExBQiA1LjAgTUFULWZpbGUsIFBsYXRmb3JtOiBQQ1dJTiwg'
                'Q3JlYXRlZCBvbjogVHVlIE9jdCAxMyAwOTowNzoxMyAyMDA5ICAgICAgICAg'
                'ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAAAUlN'
                'DwAAAKwDAAB4nOxYbW/TMBB2t26CIU2FCWnfCN/4sJWEF4mPeymCStta1qqA'
                'ACG3cTuDG1eJM7Ug/tt+GvaWtK5JiZslWUCLFKXn+p7zc3e2z94EAFw8BmCd'
                'f+/wdwVcPWuBXJJeIbcQY9gZeGugDLaD9gv+dqCLYZegDiQ+8sD0CdvrTp+2'
                'J6PpX8fU9gk6gUO5M39O/GEXuV6jHyoGfzfxGJEW/oHA/BN2O0Xn2MPUCfQD'
                'fLV1apcyxe6msLE180NJ8UOZv1tSu+j/Fsz6lyP8ti31rwRyG43Z7ika+AS6'
                'BhqPXOSJAXoCby8G766CJ+SGiwfNM+iFfhE4r2Jw1hWc9Uu/9wjCevprir6Q'
                'jyetd0eB/Tge9xR9ITcbreqnz/ZP69eXG+VxiAjxNHlExaOG+tAnrHYQtOcZ'
                '1yg+lrnzwtQcR2RcXDqCA8h4jk7HYcbglOdwyjznPaajtzqntwr2D9ta9lS9'
                'j3xuX8fv+z2+xEl+X5Yvnwlf87S/MoezAk5o8ng3mOcbbwjtQqJtvzSHUwJV'
                'oGd/Q7Ev5Bo1HMoMP0z868R/2XFbmvbUeB8j6KTJNw4nrbipfjN3LK197YFi'
                'X8gtBh0burZh8y13tlzkmgdpxdOsmlae8cxqHoTxXHb9sMzk+019CAdIc7xq'
                'vJ5r6i2KVwK9l2nUGXsx+mnlSdR+UXcYcjzMJkAfJ++8TYLjse/GkJ7jsExP'
                '0z9Z7adZ72dJ+O/7jA75etyT+KfFIy9/JK0v/lV/JOE1cOHE60EinxeyyrOi'
                '5cdNz9dF9vPWS4tvkn2/SSBDKekvm7fOU5jpOUGtG94jQq6jF/o5aZybMXqP'
                'FP8KmXM1do0Dys6MjlU1DV6tG51n/Eefunw9zBT3ycbf79XuS+2yf/ZixhOV'
                'z1jUnwOX+iN9nKjzFO1+Qz02A5LHFX7jzkkyr0ogS7gGdmw0yhBPl39Fwa3M'
                '+fEKNor/om+cPd243dT4/1f7cTi686BoOEUdV1H5xa0zUfc71GcEO+iPhabI'
                'PIuGU9Rx3fK75bfMfpT2+qF+P5QW14tqXZ203jii0L68q5Tul+J4PVRwhFy3'
                'kcNwf9J08VC+W0haz4V4LdSj4kJ9mXu9qDrg9XhEXdamNchgF3pIPXf8BgAA'
                '//9jY4AAViDmAGJGIGaB0iDABOQJCfMI8wHZBkDMBlXHgkUfI5I+ASDLEEij'
                '6yPGPlYeZi6QPgsS9LFAxbfJ3pS7LOsuB9L/Akk/IwH9IPUaeNTDwGBVDwDn'
                '9/tU/r77zw==')
        pipeline = cpp.Pipeline()
        def callback(caller,event):
            self.assertFalse(isinstance(event, cpp.LoadExceptionEvent))
        pipeline.add_listener(callback)
        pipeline.load(StringIO(zlib.decompress(base64.b64decode(data))))
        self.assertEqual(len(pipeline.modules()), 4)
        module = pipeline.modules()[-1]
        self.assertTrue(isinstance(module, E.ExportToDatabase))
        self.assertEqual(module.db_type, E.DB_MYSQL_CSV)
        self.assertEqual(module.db_name, "DefaultDB")
        self.assertEqual(module.sql_file_prefix, "SQL_")
        self.assertEqual(module.table_prefix, "Test")
        self.assertTrue(module.wants_agg_mean)
        self.assertFalse(module.wants_agg_median)
        self.assertTrue(module.wants_agg_std_dev)
        self.assertEqual(module.objects_choice, E.O_SELECT)
        self.assertEqual(len(module.objects_list.selections), 1)
        self.assertEqual(module.objects_list.selections[0], "Nuclei")
    
    def test_01_02_load_v9(self):
        data = ('eJztW91u2zYUpl0na9qhSHfTYkUBXg5DKshLXSTpxezE62Yg/lltdBi2YaMl'
                '2lEriwJFpXGHvccerY+wyz3CRFeKJVauaFlK7EUCBOXQ/M7Hc3gOeehY7cbg'
                'tHEMa4oK243Bk5FhYtgzERsROjmCFtuDJxQjhnVIrCM4cDHsagxW96F6ePS0'
                'drR/CL9R1UOQ7iq12ve8x+3nAGzzp3eX/Y+2fLkUurncx4wZ1tjZAhXw0G9/'
                '792vEDXQ0MSvkOliZ04RtLesERlM7cuP2kR3TdxBk3Bn7+q4kyGmTncUAP2P'
                'e8YFNvvGOyyYEHR7ic8NxyCWj/f1i62XvIQJvP0z8vYF9YYj6Of++fvR3D8l'
                'wT8V734cauf962DevxLjzzuh/ru+7LA3cELOjWBYMnp2BD1c7lJj3DtDTmAH'
                '13OQoGdb0MPljquZ2JDDbwl4Lren/R9Pff4fEvAPBTyXB/iCPXmJx66JKMQX'
                'NsUOn0jnuuw5wabprODPAXZY8/gDXk3AlyL4EtiX5I0bd1Xde6oCuXi6K+C5'
                '3KPERmPEPN/P2mXGfyui5xb42QvqtHnRJNAiDLpBQOfJvyifGpq35AF5/kpE'
                'T2U296uMOwlXjuDKoEPSz3eXOS783iRDZKa218v832Xy/oHAz+UmHiHXZLA1'
                'QWMMmwbFGiN0utK8L5tvVUm7s+JTwNXOlzhuda+60rjTxmde8yLGo6qo1evI'
                'v7zmQeSrqvnOQ1pc2nmIwdVk9r/PQDQ/uGxMxvpQ/div2wI+uAL8jv9Mu2+0'
                'LIYtx2DTJfTI7n9p6g/N9lTQFeqAbl/55Vf9z+pfv2Xul2XXgaCeSfLDbRDl'
                '57JOLGZj/CbL+jptvibxy8ZDkp7PBT1c9vfZ5rGiD2X1yMbFsvNZS+nHtOus'
                '7LourkMdYuE86884/w7eEqiZyHH8g+FVrtey9i7CJdV/9wV7ufwTNsZn/OuO'
                'c36wt7Rl8mxT5jkur18QiseUuJY+tzdJT9z61MemVzErirKC3xong8z8vcw+'
                'u+q5PI2/0pzvsrY7C1ye8+rVX2tp36K8rSfg0pyj1tneLPaDTbZvHfMxS7+I'
                '86fUrn+cWZ6f0tQ962xvnnXPOttdT7Bbtu7ZFHtv+rokc467knz7co4rCbi4'
                '/89dZXwb/HtsHuC2vJ649ZAMX3t1/VzRpqxroXFDw9KxnaO+Tcyr/yOuDrLJ'
                'k02xt8AVuAJX4ApcPvvFLojuF/ye7xcfyoBNsvem+TeJv6gHClweuDq43rgv'
                'cDcTVwdF3BW4Yt8rcAWuwBW4AlfgNgn3T2mOKwk4Lod/p8D7/xHiidvnvw71'
                '3/VlDZumTQl/348qk9lLaY5iEqTPCgBHOfX+nL0DEXofzE7gqQs89UU8ho4t'
                'ZoymNvXYXEYmiBma0vJbe15rI2jlvGcJvAcC70ESr4M1YumITi85+0GLDN8z'
                'ge/ZIj58YRPKGNERQ0PkYOW7WcOANP2Gj+NkJ4YvPN9lT3rw+P4Xn4ovAKJx'
                'NY+3f79Nw1eplHfugejv4+4m4CogGuezuAbLxfVXn+gf2LjO/Zf1c8m7/gOx'
                'RQ67')    
        pipeline = cpp.Pipeline()
        def callback(caller,event):
            self.assertFalse(isinstance(event, cpp.LoadExceptionEvent))
        pipeline.add_listener(callback)
        pipeline.load(StringIO(zlib.decompress(base64.b64decode(data))))
        self.assertEqual(len(pipeline.modules()), 4)
        module = pipeline.modules()[-1]
        self.assertTrue(isinstance(module, E.ExportToDatabase))
        self.assertEqual(module.db_type, E.DB_MYSQL)
        self.assertEqual(module.db_name, "TestDB")
        self.assertEqual(module.sql_file_prefix, "SQL_")
        self.assertEqual(module.table_prefix, "Test")
        self.assertEqual(module.db_host, "imgdb01")
        self.assertEqual(module.db_user, "cpuser")
        self.assertEqual(module.db_passwd, "dontpeek")
        self.assertTrue(module.wants_agg_mean)
        self.assertFalse(module.wants_agg_median)
        self.assertTrue(module.wants_agg_std_dev)
        self.assertEqual(module.objects_choice, E.O_SELECT)
        self.assertEqual(len(module.objects_list.selections), 1)
        self.assertEqual(module.objects_list.selections[0], "Cells")

    def test_01_03_load_v10(self):
        data = ('eJztW91v2zYQl10nW9phSB+GbRgK6LEdYkFOmizJhtZ27CwG/LXabVAEWUZb'
                'tM1BFgWJSu0N/X/2p+0xj3scacuRzMqVLH8jEiDYd+KPv7vj6USJUilTL2ay'
                '4qEki6VMPdlCKhSrKiAtbHRPRY3siWcGBAQqItZOxRLWxDK+FeUTUT4+PTg6'
                'PTwQ92X5RAi3xQqlr+nPPz8Lwjb9/ZLucfvQli3HXDuTa5AQpLXNLSEhfGfr'
                '7+j+DhgINFT4DqgWNB2Kkb6gtXC9r98fKmHFUmEZdN2N6Va2ug1omJXWCGgf'
                'rqIeVGvoL8i5MGr2Bt4iE2HNxtv989p7Xkw43loHfzg3qDlc/1lAmp0aoSMw'
                'rmdx6/3gxC3GxS1B92cuPWt/ITjtEx5xfupqv2vLSFPQLVIsoIqoC9r3VrP+'
                'ZJ/+Ho3190jIlTMD3LEPbpuzg8llq6lCJATCb3F4Jpf6td+Ktt1pH/wuh2d7'
                'HfZIMt8DTSJ22ZDMw49p4/eeRj8sbxHCfD0XjDc2ho8JB0L4uKfkvZey8Cnv'
                'NocfbSP8jv0bxN74GG9cKONg4/yYs5fJOSxqmIiWCYPzTxqnsP6GiXO+p5Ob'
                'GeM1D9w8xzUxxpcQ6Bl8E6SOfcvFh8k52AKWSsQCK2JiDhmwSbDRX8n4Lpsv'
                '7cP3hIsXkyvEtMRfVdwAqqfd8/SXrzfSHOMUBJeS5JXUp7C4MNdxWZIH217K'
                '/jPB/nX2e9p6QX1OLbIOfyGMx5nJqNtWGnJqoefrDsfL5IJGoGYi0nf1syi/'
                'veYXTZ1eMo3w9p91gKZBdT+56XGoWuaBMdv8eNrzIyXP5mfah+8rzk8m29fT'
                'XFZSGqN+pq3zqZC4nzxwy7j++sXJKx/P2Q215tzXreN8Y1K97fngLjh/mfy7'
                'fSJfpZL718krOXly/ff+x+Tz19VfLvPF4s2byuWrq0zy4vqFozurFN+Wyq9G'
                'jV9IBLUWNX9fRtw6Prhjzm4ms2C8h8Cwo/Dy4zA+JayRjhOZgS4H+o5mk/Jp'
                'U+bLD51v1eMnzzgfT/vwedXpGlTpHaEkSRPsXuR9bRlrcNnzlEnPoTYlj5aN'
                'W/Z5uY7+ydLhyu1c9HOP+gcsNlVgmvaT7k3y98LHX6/nApcQtTtseeeWLWRo'
                'zUnz1HX2O+3jt9c88RwbsG1gS1M2z9+HXpf4+8HDFdl5972Di3E4r/W3Zeb3'
                'YLGOJbgevB+veogbf9J5kdPRptQ1l90i0hSoz8GOCBfhIlyEi3ARLsJFuIeC'
                'S7twQd+Xcuafw+nXJvkb4R4mLi1EeR7hIlyEW496E/S5zqb4G+EiXISLcBEu'
                'wm0y7r+Yg+PXfZjsfr+Dtf/DxeN1nf/R1X7XlptQVXUDs+/xDKk7+GjMlFQM'
                'lOFXWFKR/i24PshiPLoPT5rjSU/iQQrUCGr1dYOyWQR3AUFNqWBrq1SbGWkZ'
                'r997glmONzuJtwuBaRlwuHYDDCp1gA6l0lBdGagzVF1jasfvjg//Ecd/NIkf'
                '9nRsEIIVQEADmFDKDxR1nLMVn+bNjgefe/zjVHr6LP7N5/JNEMbzzMm/u9dh'
                '+BKJ2GOGc78X9MQHlxDG857h/xWmy/Pnn2k/8nGd208b5xjdZo2Tw5O4t2nY'
                '/3q2/x/7Ruk9')
        pipeline = cpp.Pipeline()
        def callback(caller,event):
            self.assertFalse(isinstance(event, cpp.LoadExceptionEvent))
        pipeline.add_listener(callback)
        pipeline.load(StringIO(zlib.decompress(base64.b64decode(data))))
        #
        # Export to database is the last module of four
        #
        # MySQL database
        # Don't store in CSV file
        # DB name = LeeETD 
        # host is imgdb01
        # user name is cpuser
        # don't add a prefix
        # calculate only aggregate mean per image
        # calculate only aggregate median per well
        # Select objects to include
        # include nuclei
        #
        self.assertEqual(len(pipeline.modules()), 4)
        module = pipeline.modules()[-1]
        self.assertTrue(isinstance(module, E.ExportToDatabase))
        self.assertEqual(module.db_type, E.DB_MYSQL)
        self.assertEqual(module.db_host, "imgdb01")
        self.assertEqual(module.db_name, "LeeETD")
        self.assertEqual(module.db_user, "cpuser")
        self.assertFalse(module.want_table_prefix)
        self.assertTrue(module.wants_agg_mean)
        self.assertFalse(module.wants_agg_median)
        self.assertFalse(module.wants_agg_std_dev)
        self.assertFalse(module.wants_agg_mean_well)
        self.assertTrue(module.wants_agg_median_well)
        self.assertFalse(module.wants_agg_std_dev_well)
        self.assertEqual(module.objects_choice, E.O_SELECT)
        self.assertEqual(module.objects_list.value, "Nuclei")
        
    def test_01_04_load_v11(self):
        data = r"""CellProfiler Pipeline: http://www.cellprofiler.org
Version:1
SVNRevision:8952

LoadText:[module_num:1|svn_version:\'Unknown\'|variable_revision_number:3|show_window:False|notes:\x5B\x5D]
    CSV file location:Default Input Folder
    Path to the CSV file:.
    Name of the CSV file:1049.csv
    Load images from CSV data?:Yes
    Image folder location:Default Input Folder
    Path to the images:.
    Process just a range of rows?:No
    Rows to process:1,100000
    Group images by metadata?:No
    Select metadata fields for grouping:

ExportToDatabase:[module_num:2|svn_version:\'8947\'|variable_revision_number:11|show_window:False|notes:\x5B\x5D]
    Database type:MySQL
    Database name:DefaultDB
    Add a prefix to table names?:No
    Table prefix:Expt_
    SQL file prefix:SQL_
    Where do you want to save files?:Custom folder with metadata
    Enter the output folder:./\\g<Plate>
    Create a CellProfiler Analyst properties file?:No
    Store the database in CSV files? :Yes
    Database host:
    Username:
    Password:
    Name the SQLite database file:DefaultDB.db
    Calculate the per-image mean values of object measurements?:Yes
    Calculate the per-image median values of object measurements?:No
    Calculate the per-image standard deviation values of object measurements?:No
    Calculate the per-well mean values of object measurements?:No
    Calculate the per-well median values of object measurements?:No
    Calculate the per-well standard deviation values of object measurements?:No
    Export measurements for all objects to the database?:All
    Select the objects:
"""
        pipeline = cpp.Pipeline()
        def callback(caller,event):
            self.assertFalse(isinstance(event, cpp.LoadExceptionEvent))
        pipeline.add_listener(callback)
        pipeline.load(StringIO(data))
        self.assertEqual(len(pipeline.modules()), 2)
        module = pipeline.modules()[-1]
        self.assertTrue(isinstance(module, E.ExportToDatabase))
        self.assertEqual(module.db_type, E.DB_MYSQL_CSV)
        self.assertEqual(module.directory_choice, E.DIR_CUSTOM_WITH_METADATA)
        self.assertEqual(module.output_directory, r"./\g<Plate>")
        self.assertEqual(module.sql_file_prefix, "SQL_")
        self.assertEqual(module.db_name, "DefaultDB")
        
    def test_01_05_load_v12(self):
        data = r"""CellProfiler Pipeline: http://www.cellprofiler.org
Version:1
SVNRevision:8952

LoadText:[module_num:1|svn_version:\'Unknown\'|variable_revision_number:3|show_window:False|notes:\x5B\x5D]
    CSV file location:Default Input Folder
    Path to the CSV file:.
    Name of the CSV file:1049.csv
    Load images from CSV data?:Yes
    Image folder location:Default Input Folder
    Path to the images:.
    Process just a range of rows?:No
    Rows to process:1,100000
    Group images by metadata?:No
    Select metadata fields for grouping:

ExportToDatabase:[module_num:2|svn_version:\'8947\'|variable_revision_number:12|show_window:False|notes:\x5B\x5D]
    Database type:MySQL
    Database name:DefaultDB
    Add a prefix to table names?:No
    Table prefix:Expt_
    SQL file prefix:SQL_
    Where do you want to save files?:Custom folder with metadata
    Enter the output folder:./\\g<Plate>
    Create a CellProfiler Analyst properties file?:No
    Database host:
    Username:
    Password:
    Name the SQLite database file:DefaultDB.db
    Calculate the per-image mean values of object measurements?:Yes
    Calculate the per-image median values of object measurements?:No
    Calculate the per-image standard deviation values of object measurements?:No
    Calculate the per-well mean values of object measurements?:No
    Calculate the per-well median values of object measurements?:No
    Calculate the per-well standard deviation values of object measurements?:No
    Export measurements for all objects to the database?:All
    Select the objects:
"""
        pipeline = cpp.Pipeline()
        def callback(caller,event):
            self.assertFalse(isinstance(event, cpp.LoadExceptionEvent))
        pipeline.add_listener(callback)
        pipeline.load(StringIO(data))
        self.assertEqual(len(pipeline.modules()), 2)
        module = pipeline.modules()[-1]
        self.assertTrue(isinstance(module, E.ExportToDatabase))
        self.assertEqual(module.db_type, E.DB_MYSQL)
        self.assertEqual(module.directory_choice, E.DIR_CUSTOM_WITH_METADATA)
        self.assertEqual(module.output_directory, r"./\g<Plate>")
        self.assertEqual(module.sql_file_prefix, "SQL_")
        self.assertEqual(module.db_name, "DefaultDB")
        self.assertEqual(module.max_column_size, 64)
        
    def test_01_06_load_v13(self):
        data = r"""CellProfiler Pipeline: http://www.cellprofiler.org
Version:1
SVNRevision:8952

LoadText:[module_num:1|svn_version:\'Unknown\'|variable_revision_number:3|show_window:False|notes:\x5B\x5D]
    CSV file location:Default Input Folder
    Path to the CSV file:.
    Name of the CSV file:1049.csv
    Load images from CSV data?:Yes
    Image folder location:Default Input Folder
    Path to the images:.
    Process just a range of rows?:No
    Rows to process:1,100000
    Group images by metadata?:No
    Select metadata fields for grouping:

ExportToDatabase:[module_num:2|svn_version:\'8947\'|variable_revision_number:12|show_window:False|notes:\x5B\x5D]
    Database type:MySQL
    Database name:DefaultDB
    Add a prefix to table names?:No
    Table prefix:Expt_
    SQL file prefix:SQL_
    Where do you want to save files?:Custom folder with metadata
    Enter the output folder:./\\g<Plate>
    Create a CellProfiler Analyst properties file?:No
    Database host:
    Username:
    Password:
    Name the SQLite database file:DefaultDB.db
    Calculate the per-image mean values of object measurements?:Yes
    Calculate the per-image median values of object measurements?:No
    Calculate the per-image standard deviation values of object measurements?:No
    Calculate the per-well mean values of object measurements?:No
    Calculate the per-well median values of object measurements?:No
    Calculate the per-well standard deviation values of object measurements?:No
    Export measurements for all objects to the database?:All
    Select the objects:
    Maximum # of characters in a column name:61
"""
        pipeline = cpp.Pipeline()
        def callback(caller,event):
            self.assertFalse(isinstance(event, cpp.LoadExceptionEvent))
        pipeline.add_listener(callback)
        pipeline.load(StringIO(data))
        self.assertEqual(len(pipeline.modules()), 2)
        module = pipeline.modules()[-1]
        self.assertTrue(isinstance(module, E.ExportToDatabase))
        self.assertEqual(module.db_type, E.DB_MYSQL)
        self.assertEqual(module.directory_choice, E.DIR_CUSTOM_WITH_METADATA)
        self.assertEqual(module.output_directory, r"./\g<Plate>")
        self.assertEqual(module.sql_file_prefix, "SQL_")
        self.assertEqual(module.db_name, "DefaultDB")
        self.assertEqual(module.max_column_size, 61)
        
    def make_workspace(self, wants_files, alt_object=False, 
                       long_measurement=False, wierd_measurement=False,
                       well_metadata = False):
        '''Make a measurements structure with image and object measurements'''
        class TestModule(cpm.CPModule):
            module_name = "TestModule"
            module_num = 1
            def __init__(self):
                self.image_name = cps.ImageNameProvider("Foo", IMAGE_NAME)
                self.objects_name = cps.ObjectNameProvider("Bar", OBJECT_NAME)
                if alt_object:
                    self.altobjects_name = cps.ObjectNameProvider("Baz", ALTOBJECT_NAME)
            
            def settings(self):
                return [self.image_name, self.objects_name] + (
                    [self.altobjects_name] if alt_object else [])
            
            def get_measurement_columns(self, pipeline):
                columns = [(cpmeas.IMAGE, INT_IMG_MEASUREMENT, cpmeas.COLTYPE_INTEGER),
                           (cpmeas.IMAGE, FLOAT_IMG_MEASUREMENT, cpmeas.COLTYPE_FLOAT),
                           (cpmeas.IMAGE, STRING_IMG_MEASUREMENT, 
                            cpmeas.COLTYPE_VARCHAR_FORMAT % 40),
                           (cpmeas.IMAGE, OBJECT_COUNT_MEASUREMENT, cpmeas.COLTYPE_INTEGER),
                           (OBJECT_NAME, I.M_NUMBER_OBJECT_NUMBER, cpmeas.COLTYPE_INTEGER),
                           (OBJECT_NAME, OBJ_MEASUREMENT, cpmeas.COLTYPE_FLOAT)]
                if alt_object:
                    columns += [(cpmeas.IMAGE, ALTOBJECT_COUNT_MEASUREMENT, cpmeas.COLTYPE_INTEGER),
                                (ALTOBJECT_NAME, I.M_NUMBER_OBJECT_NUMBER, cpmeas.COLTYPE_INTEGER),
                                (ALTOBJECT_NAME, OBJ_MEASUREMENT, cpmeas.COLTYPE_FLOAT)]
                if long_measurement:
                    columns += [(cpmeas.IMAGE,LONG_IMG_MEASUREMENT,cpmeas.COLTYPE_INTEGER),
                                (OBJECT_NAME, LONG_OBJ_MEASUREMENT, cpmeas.COLTYPE_FLOAT)]
                if wierd_measurement:
                    columns += [(cpmeas.IMAGE,WIERD_IMG_MEASUREMENT,cpmeas.COLTYPE_INTEGER),
                                (OBJECT_NAME, WIERD_OBJ_MEASUREMENT, cpmeas.COLTYPE_FLOAT)]
                if well_metadata:
                    columns += [
                        (cpmeas.IMAGE, "Metadata_Plate", cpmeas.COLTYPE_VARCHAR_FORMAT % 20),
                        (cpmeas.IMAGE, "Metadata_Well", cpmeas.COLTYPE_VARCHAR_FORMAT % 3)]
                return columns
            
            def get_categories(self, pipeline, object_name):
                return ([M_CATEGORY, I.C_NUMBER] 
                        if (object_name == OBJECT_NAME or 
                            ((object_name == ALTOBJECT_NAME) and alt_object))
                        else [M_CATEGORY, "Count", "Metadata"] 
                        if object_name == cpmeas.IMAGE
                        else [])
            
            def get_measurements(self, pipeline, object_name, category):
                if category == M_CATEGORY:
                    if object_name == OBJECT_NAME:
                        if long_measurement:
                            return [OBJ_FEATURE, LONG_OBJ_FEATURE]
                        else:
                            return [OBJ_FEATURE]
                    elif (object_name == ALTOBJECT_NAME) and alt_object:
                        return [OBJ_FEATURE]
                    else:
                        return ([INT_IMG_FEATURE, FLOAT_IMG_FEATURE, STRING_IMG_FEATURE] +
                                [ LONG_IMG_FEATURE] if long_measurement 
                                else [WIERD_IMG_FEATURE] if wierd_measurement
                                else [])
                elif category == I.C_NUMBER and object_name in (OBJECT_NAME, ALTOBJECT_NAME):
                    return I.FTR_OBJECT_NUMBER
                elif category == "Count" and object_name == cpmeas.IMAGE:
                    result = [OBJECT_NAME]
                    if alt_object:
                        result += [ALTOBJECT_NAME]
                    return result
                elif category == "Metadata" and object_name == cpmeas.IMAGE:
                    return ["Plate", "Well"]
                return []
            
        m = cpmeas.Measurements()
        m.add_image_measurement(INT_IMG_MEASUREMENT, INT_VALUE)
        m.add_image_measurement(FLOAT_IMG_MEASUREMENT, FLOAT_VALUE)
        m.add_image_measurement(STRING_IMG_MEASUREMENT, STRING_VALUE)
        m.add_image_measurement(OBJECT_COUNT_MEASUREMENT, len(OBJ_VALUE))
        m.add_measurement(OBJECT_NAME, I.M_NUMBER_OBJECT_NUMBER, 
                          np.arange(len(OBJ_VALUE)) + 1)
        m.add_measurement(OBJECT_NAME, OBJ_MEASUREMENT, OBJ_VALUE.copy())
        if alt_object:
            m.add_measurement(ALTOBJECT_NAME, I.M_NUMBER_OBJECT_NUMBER, 
                              np.arange(100) + 1)
            m.add_image_measurement(ALTOBJECT_COUNT_MEASUREMENT, 100)
            m.add_measurement(ALTOBJECT_NAME, OBJ_MEASUREMENT,
                              np.arange(100))
        if long_measurement:
            m.add_image_measurement(LONG_IMG_MEASUREMENT, 100)
            m.add_measurement(OBJECT_NAME, LONG_OBJ_MEASUREMENT, OBJ_VALUE.copy())
        if wierd_measurement:
            m.add_image_measurement(WIERD_IMG_MEASUREMENT, 100)
            m.add_measurement(OBJECT_NAME, WIERD_OBJ_MEASUREMENT, OBJ_VALUE.copy())
        if well_metadata:
            m.add_image_measurement("Metadata_Plate", PLATE)
            m.add_image_measurement("Metadata_Well", WELL)
        image_set_list = cpi.ImageSetList()
        image_set = image_set_list.get_image_set(0)
        image_set.add(IMAGE_NAME, cpi.Image(np.zeros((10,10))))
        object_set = cpo.ObjectSet()
        objects = cpo.Objects()
        objects.segmented = np.array([[0,1,2,3],[0,1,2,3]])
        object_set.add_objects(objects, OBJECT_NAME)
        if alt_object:
            objects = cpo.Objects()
            objects.segmented = np.array([[0,1,2,3],[0,1,2,3]])
            object_set.add_objects(objects, ALTOBJECT_NAME)
        test_module = TestModule()
        pipeline = cpp.Pipeline()
        def callback_handler(caller, event):
            self.assertFalse(isinstance(event, cpp.RunExceptionEvent))
        
        pipeline.add_listener(callback_handler)
        pipeline.add_module(test_module)
        module = E.ExportToDatabase()
        module.module_num = 2
        table_prefix = "T_%s"%str(uuid.uuid4()).replace('-','')
        module.table_prefix.value = table_prefix
        module.want_table_prefix.value = True
        module.db_host.value = 'imgdb01'
        module.db_user.value = 'cpuser'
        module.db_passwd.value = 'cPus3r'
        module.db_name.value ='CPUnitTest'
        pipeline.add_module(module)
        workspace = cpw.Workspace(pipeline, module, image_set,
                                  object_set, m, image_set_list)
        for column in pipeline.get_measurement_columns():
            if (column[1].startswith("ModuleError_") or
                column[1].startswith("ExecutionTime_")):
                m.add_image_measurement(column[1],0)
        if wants_files or well_metadata:
            output_dir = tempfile.mkdtemp()
            module.directory_choice.value = E.DIR_CUSTOM
            module.output_directory.value = output_dir
            def finally_fn():
                for filename in os.listdir(output_dir):
                    os.remove(os.path.join(output_dir, filename))
            return workspace, module, output_dir, finally_fn
        else:
            return workspace, module
        
    def test_02_01_write_mysql_db(self):
        workspace, module, output_dir, finally_fn = self.make_workspace(True)
        os.chdir(output_dir)
        try:
            self.assertTrue(isinstance(module, E.ExportToDatabase))
            module.db_type = E.DB_MYSQL_CSV
            module.wants_agg_mean.value = False
            module.wants_agg_median.value = False
            module.wants_agg_std_dev.value = False
            module.objects_choice.value = E.O_ALL
            module.directory_choice.value = E.DIR_CUSTOM
            module.output_directory.value = output_dir
            module.separate_object_tables.value = E.OT_COMBINE
            module.post_run(workspace)
            sql_file = os.path.join(output_dir, "SQL__SETUP.SQL")
            base_name = "SQL_1_1"
            image_file = os.path.join(output_dir, base_name+"_image.CSV")
            object_file = os.path.join(output_dir, base_name+"_object.CSV")
            for filename in (sql_file, image_file, object_file):
                self.assertTrue(os.path.isfile(filename))
            fd = open(sql_file,'rt')
            sql_text = fd.read()
            fd.close()
            for statement in sql_text.split(';'):
                if len(statement.strip()) == 0:
                    continue
                self.cursor.execute(statement)
            #
            # Now read the image file from the database
            #
            image_table = module.table_prefix.value + "Per_Image"
            statement = ("select ImageNumber, Image_%s, Image_%s, Image_%s, Image_Count_%s "
                         "from %s" %
                         (INT_IMG_MEASUREMENT, FLOAT_IMG_MEASUREMENT,
                          STRING_IMG_MEASUREMENT, OBJECT_NAME, image_table))
            self.cursor.execute(statement)
            row = self.cursor.fetchone()
            self.assertEqual(len(row), 5)
            self.assertEqual(row[0],1)
            self.assertAlmostEqual(row[1], INT_VALUE)
            self.assertAlmostEqual(row[2], FLOAT_VALUE)
            self.assertEqual(row[3], STRING_VALUE)
            self.assertEqual(row[4], len(OBJ_VALUE))
            self.assertRaises(StopIteration, self.cursor.next)
            statement = ("select ImageNumber, ObjectNumber, %s_%s "
                         "from %sPer_Object order by ObjectNumber"%
                         (OBJECT_NAME, OBJ_MEASUREMENT, module.table_prefix.value))
            self.cursor.execute(statement)
            for i, value in enumerate(OBJ_VALUE):
                row = self.cursor.fetchone()
                self.assertEqual(len(row), 3)
                self.assertEqual(row[0], 1)
                self.assertEqual(row[1], i+1)
                self.assertAlmostEqual(row[2], value)
            self.assertRaises(StopIteration, self.cursor.next)
        finally:
            os.chdir(output_dir)
            finally_fn()
            for table_suffix in ("Per_Image","Per_Object"):
                table_name = module.table_prefix.value + table_suffix
                try:
                    self.cursor.execute("drop table %s.%s" %
                                        (module.db_name.value, table_name))
                except:
                    print "Failed to drop table %s"%table_name
    
    def test_02_015_write_mysql_db_filter_objs(self):
        workspace, module, output_dir, finally_fn = self.make_workspace(True, True)
        os.chdir(output_dir)
        try:
            self.assertTrue(isinstance(module, E.ExportToDatabase))
            module.db_type = E.DB_MYSQL_CSV
            module.wants_agg_mean.value = False
            module.wants_agg_median.value = False
            module.wants_agg_std_dev.value = False
            module.objects_choice.value = E.O_SELECT
            module.objects_list.choices = [OBJECT_NAME, ALTOBJECT_NAME]
            module.objects_list.value = OBJECT_NAME
            module.directory_choice.value = E.DIR_CUSTOM
            module.output_directory.value = output_dir
            module.separate_object_tables.value = E.OT_COMBINE
            module.post_run(workspace)
            sql_file = os.path.join(output_dir, "SQL__SETUP.SQL")
            base_name = "SQL_1_1"
            image_file = os.path.join(output_dir, base_name+"_image.CSV")
            object_file = os.path.join(output_dir, base_name+"_object.CSV")
            for filename in (sql_file, image_file, object_file):
                self.assertTrue(os.path.isfile(filename))
            fd = open(sql_file,'rt')
            sql_text = fd.read()
            fd.close()
            for statement in sql_text.split(';'):
                if len(statement.strip()) == 0:
                    continue
                self.cursor.execute(statement)
            #
            # Now read the image file from the database
            #
            image_table = module.table_prefix.value + "Per_Image"
            statement = ("select ImageNumber, Image_%s, Image_%s, Image_%s, Image_Count_%s "
                         "from %s" %
                         (INT_IMG_MEASUREMENT, FLOAT_IMG_MEASUREMENT,
                          STRING_IMG_MEASUREMENT, OBJECT_NAME, image_table))
            self.cursor.execute(statement)
            row = self.cursor.fetchone()
            self.assertEqual(len(row), 5)
            self.assertEqual(row[0],1)
            self.assertAlmostEqual(row[1], INT_VALUE)
            self.assertAlmostEqual(row[2], FLOAT_VALUE)
            self.assertEqual(row[3], STRING_VALUE)
            self.assertEqual(row[4], len(OBJ_VALUE))
            self.assertRaises(StopIteration, self.cursor.next)
            statement = ("select ImageNumber, ObjectNumber, %s_%s "
                         "from %sPer_Object order by ObjectNumber"%
                         (OBJECT_NAME, OBJ_MEASUREMENT, module.table_prefix.value))
            self.cursor.execute(statement)
            for i, value in enumerate(OBJ_VALUE):
                row = self.cursor.fetchone()
                self.assertEqual(len(row), 3)
                self.assertEqual(row[0], 1)
                self.assertEqual(row[1], i+1)
                self.assertAlmostEqual(row[2], value)
            self.assertRaises(StopIteration, self.cursor.next)
        finally:
            os.chdir(output_dir)
            finally_fn()
            for table_suffix in ("Per_Image","Per_Object"):
                table_name = module.table_prefix.value + table_suffix
                try:
                    self.cursor.execute("drop table %s.%s" %
                                        (module.db_name.value, table_name))
                except:
                    print "Failed to drop table %s"%table_name

    def test_02_02_mysql_direct(self):
        '''Write directly to the mysql DB, not to a file'''
        workspace, module = self.make_workspace(False)
        try:
            self.assertTrue(isinstance(module, E.ExportToDatabase))
            module.db_type = E.DB_MYSQL
            module.wants_agg_mean.value = False
            module.wants_agg_median.value = False
            module.wants_agg_std_dev.value = False
            module.objects_choice.value = E.O_ALL
            module.separate_object_tables.value = E.OT_COMBINE
            module.prepare_run(workspace.pipeline, workspace.image_set_list,None)
            module.prepare_group(workspace.pipeline, workspace.image_set_list,
                                 {}, [1])
            module.run(workspace)
            self.cursor.execute("use CPUnitTest")
            #
            # Now read the image file from the database
            #
            image_table = module.table_prefix.value + "Per_Image"
            statement = ("select ImageNumber, Image_%s, Image_%s, Image_%s, Image_Count_%s "
                         "from %s" %
                         (INT_IMG_MEASUREMENT, FLOAT_IMG_MEASUREMENT,
                          STRING_IMG_MEASUREMENT, OBJECT_NAME, image_table))
            self.cursor.execute(statement)
            row = self.cursor.fetchone()
            self.assertEqual(len(row), 5)
            self.assertEqual(row[0],1)
            self.assertAlmostEqual(row[1], INT_VALUE)
            self.assertAlmostEqual(row[2], FLOAT_VALUE)
            self.assertEqual(row[3], STRING_VALUE)
            self.assertEqual(row[4], len(OBJ_VALUE))
            self.assertRaises(StopIteration, self.cursor.next)
            statement = ("select ImageNumber, ObjectNumber, %s_%s "
                         "from %sPer_Object order by ObjectNumber"%
                         (OBJECT_NAME, OBJ_MEASUREMENT, module.table_prefix.value))
            self.cursor.execute(statement)
            for i, value in enumerate(OBJ_VALUE):
                row = self.cursor.fetchone()
                self.assertEqual(len(row), 3)
                self.assertEqual(row[0], 1)
                self.assertEqual(row[1], i+1)
                self.assertAlmostEqual(row[2], value)
            self.assertRaises(StopIteration, self.cursor.next)
        finally:
            for table_suffix in ("Per_Image","Per_Object"):
                table_name = module.table_prefix.value + table_suffix
                try:
                    self.cursor.execute("drop table %s.%s" %
                                        (module.db_name.value, table_name))
                except:
                    print "Failed to drop table %s"%table_name
    
    def test_02_03_write_direct_long_colname(self):
        '''Write to MySQL, ensuring some columns have long names'''
        workspace, module = self.make_workspace(False, long_measurement=True)
        try:
            self.assertTrue(isinstance(module, E.ExportToDatabase))
            module.db_type = E.DB_MYSQL
            module.wants_agg_mean.value = False
            module.wants_agg_median.value = False
            module.wants_agg_std_dev.value = False
            module.objects_choice.value = E.O_ALL
            module.separate_object_tables.value = E.OT_COMBINE
            module.prepare_run(workspace.pipeline, workspace.image_set_list,None)
            module.prepare_group(workspace.pipeline, workspace.image_set_list,
                                 {}, [1])
            module.run(workspace)
            mappings = module.get_column_name_mappings(workspace.pipeline,
                                                       workspace.image_set_list)
            long_img_column = mappings["Image_%s"%LONG_IMG_MEASUREMENT]
            long_obj_column = mappings["%s_%s"%(OBJECT_NAME, LONG_OBJ_MEASUREMENT)]
            
            self.cursor.execute("use CPUnitTest")
            #
            # Now read the image file from the database
            #
            image_table = module.table_prefix.value + "Per_Image"
            statement = ("select ImageNumber, Image_%s, Image_%s, Image_%s,"
                         "Image_Count_%s, %s "
                         "from %s" %
                         (INT_IMG_MEASUREMENT, FLOAT_IMG_MEASUREMENT,
                          STRING_IMG_MEASUREMENT, OBJECT_NAME,
                          long_img_column, image_table))
            self.cursor.execute(statement)
            row = self.cursor.fetchone()
            self.assertEqual(len(row), 6)
            self.assertEqual(row[0],1)
            self.assertAlmostEqual(row[1], INT_VALUE)
            self.assertAlmostEqual(row[2], FLOAT_VALUE)
            self.assertEqual(row[3], STRING_VALUE)
            self.assertEqual(row[4], len(OBJ_VALUE))
            self.assertEqual(row[5], 100)
            self.assertRaises(StopIteration, self.cursor.next)
            statement = ("select ImageNumber, ObjectNumber, %s_%s,%s "
                         "from %sPer_Object order by ObjectNumber"%
                         (OBJECT_NAME, OBJ_MEASUREMENT, long_obj_column,
                          module.table_prefix.value))
            self.cursor.execute(statement)
            for i, value in enumerate(OBJ_VALUE):
                row = self.cursor.fetchone()
                self.assertEqual(len(row), 4)
                self.assertEqual(row[0], 1)
                self.assertEqual(row[1], i+1)
                self.assertAlmostEqual(row[2], value)
                self.assertAlmostEqual(row[3], value)
            self.assertRaises(StopIteration, self.cursor.next)
        finally:
            for table_suffix in ("Per_Image","Per_Object"):
                table_name = module.table_prefix.value + table_suffix
                try:
                    self.cursor.execute("drop table %s.%s" %
                                        (module.db_name.value, table_name))
                except:
                    print "Failed to drop table %s"%table_name
        
    def test_02_04_write_nulls(self):
        workspace, module, output_dir, finally_fn = self.make_workspace(True)
        #
        # Insert a NaN into the float image measurement and one of the
        # object measurements
        #
        m = workspace.measurements
        fim = m.get_all_measurements(cpmeas.IMAGE, FLOAT_IMG_MEASUREMENT)
        fim[0] = np.NaN
        om = m.get_all_measurements(OBJECT_NAME, OBJ_MEASUREMENT)
        om[0][0] = np.NaN
        os.chdir(output_dir)
        try:
            self.assertTrue(isinstance(module, E.ExportToDatabase))
            module.db_type = E.DB_MYSQL_CSV
            module.wants_agg_mean.value = True
            module.wants_agg_median.value = False
            module.wants_agg_std_dev.value = False
            module.objects_choice.value = E.O_ALL
            module.directory_choice.value = E.DIR_CUSTOM
            module.output_directory.value = output_dir
            module.separate_object_tables.value = E.OT_COMBINE
            module.post_run(workspace)
            sql_file = os.path.join(output_dir, "SQL__SETUP.SQL")
            base_name = "SQL_1_1"
            image_file = os.path.join(output_dir, base_name+"_image.CSV")
            object_file = os.path.join(output_dir, base_name+"_object.CSV")
            for filename in (sql_file, image_file, object_file):
                self.assertTrue(os.path.isfile(filename))
            fd = open(sql_file,'rt')
            sql_text = fd.read()
            fd.close()
            for statement in sql_text.split(';'):
                if len(statement.strip()) == 0:
                    continue
                self.cursor.execute(statement)
            #
            # Now read the image file from the database
            #
            image_table = module.table_prefix.value + "Per_Image"
            statement = ("select ImageNumber, Image_%s, Image_%s, Image_%s, "
                         "Image_Count_%s, Mean_%s_%s "
                         "from %s" %
                         (INT_IMG_MEASUREMENT, FLOAT_IMG_MEASUREMENT,
                          STRING_IMG_MEASUREMENT, OBJECT_NAME, OBJECT_NAME,
                          OBJ_MEASUREMENT, image_table))
            self.cursor.execute(statement)
            row = self.cursor.fetchone()
            self.assertEqual(len(row), 6)
            self.assertEqual(row[0],1)
            self.assertAlmostEqual(row[1], INT_VALUE)
            self.assertTrue(row[2] is None)
            self.assertEqual(row[3], STRING_VALUE)
            self.assertEqual(row[4], len(OBJ_VALUE))
            self.assertAlmostEqual(row[5], np.mean(om[0][~np.isnan(om[0])]))
            self.assertRaises(StopIteration, self.cursor.next)
            statement = ("select ImageNumber, ObjectNumber, %s_%s "
                         "from %sPer_Object order by ObjectNumber"%
                         (OBJECT_NAME, OBJ_MEASUREMENT, module.table_prefix.value))
            self.cursor.execute(statement)
            for i, value in enumerate(OBJ_VALUE):
                row = self.cursor.fetchone()
                self.assertEqual(len(row), 3)
                self.assertEqual(row[0], 1)
                self.assertEqual(row[1], i+1)
                if i == 0:
                    self.assertTrue(row[2] is None)
                else:
                    self.assertAlmostEqual(row[2], value)
            self.assertRaises(StopIteration, self.cursor.next)
        finally:
            os.chdir(output_dir)
            finally_fn()
            for table_suffix in ("Per_Image","Per_Object"):
                table_name = module.table_prefix.value + table_suffix
                try:
                    self.cursor.execute("drop table %s.%s" %
                                        (module.db_name.value, table_name))
                except:
                    print "Failed to drop table %s"%table_name
    
    def test_02_05_mysql_direct_null(self):
        '''Write directly to the mysql DB, not to a file and write nulls'''
        workspace, module = self.make_workspace(False)
        #
        # Insert a NaN into the float image measurement and one of the
        # object measurements
        #
        m = workspace.measurements
        fim = m.get_all_measurements(cpmeas.IMAGE, FLOAT_IMG_MEASUREMENT)
        fim[0] = np.NaN
        om = m.get_all_measurements(OBJECT_NAME, OBJ_MEASUREMENT)
        om[0][:] = np.NaN
        try:
            self.assertTrue(isinstance(module, E.ExportToDatabase))
            module.db_type = E.DB_MYSQL
            module.wants_agg_mean.value = True
            module.wants_agg_median.value = False
            module.wants_agg_std_dev.value = False
            module.objects_choice.value = E.O_ALL
            module.separate_object_tables.value = E.OT_COMBINE
            module.prepare_run(workspace.pipeline, workspace.image_set_list,None)
            module.prepare_group(workspace.pipeline, workspace.image_set_list,
                                 {}, [1])
            module.run(workspace)
            self.cursor.execute("use CPUnitTest")
            #
            # Now read the image file from the database
            #
            image_table = module.table_prefix.value + "Per_Image"
            statement = ("select ImageNumber, Image_%s, Image_%s, Image_%s, "
                         "Image_Count_%s, Mean_%s_%s "
                         "from %s" %
                         (INT_IMG_MEASUREMENT, FLOAT_IMG_MEASUREMENT,
                          STRING_IMG_MEASUREMENT, OBJECT_NAME,
                          OBJECT_NAME, OBJ_MEASUREMENT, image_table))
            self.cursor.execute(statement)
            row = self.cursor.fetchone()
            self.assertEqual(len(row), 6)
            self.assertEqual(row[0],1)
            self.assertAlmostEqual(row[1], INT_VALUE)
            self.assertTrue(row[2] is None)
            self.assertEqual(row[3], STRING_VALUE)
            self.assertEqual(row[4], len(OBJ_VALUE))
            self.assertTrue(row[5] is None)
            self.assertRaises(StopIteration, self.cursor.next)
            statement = ("select ImageNumber, ObjectNumber, %s_%s "
                         "from %sPer_Object order by ObjectNumber"%
                         (OBJECT_NAME, OBJ_MEASUREMENT, module.table_prefix.value))
            self.cursor.execute(statement)
            for i, value in enumerate(OBJ_VALUE):
                row = self.cursor.fetchone()
                self.assertEqual(len(row), 3)
                self.assertEqual(row[0], 1)
                self.assertEqual(row[1], i+1)
                self.assertTrue(row[2] is None)
            self.assertRaises(StopIteration, self.cursor.next)
        finally:
            for table_suffix in ("Per_Image","Per_Object"):
                table_name = module.table_prefix.value + table_suffix
                try:
                    self.cursor.execute("drop table %s.%s" %
                                        (module.db_name.value, table_name))
                except:
                    print "Failed to drop table %s"%table_name
                    
    def test_02_06_write_direct_wierd_colname(self):
        '''Write to MySQL, even if illegal characters are in the column name'''
        workspace, module = self.make_workspace(False, wierd_measurement=True)
        try:
            self.assertTrue(isinstance(module, E.ExportToDatabase))
            module.db_type = E.DB_MYSQL
            module.wants_agg_mean.value = False
            module.wants_agg_median.value = False
            module.wants_agg_std_dev.value = False
            module.objects_choice.value = E.O_ALL
            module.separate_object_tables.value = E.OT_COMBINE
            module.prepare_run(workspace.pipeline, workspace.image_set_list,None)
            module.prepare_group(workspace.pipeline, workspace.image_set_list,
                                 {}, [1])
            module.run(workspace)
            mappings = module.get_column_name_mappings(workspace.pipeline,
                                                       workspace.image_set_list)
            wierd_img_column = mappings["Image_%s"%WIERD_IMG_MEASUREMENT]
            wierd_obj_column = mappings["%s_%s"%(OBJECT_NAME, WIERD_OBJ_MEASUREMENT)]
            
            self.cursor.execute("use CPUnitTest")
            #
            # Now read the image file from the database
            #
            image_table = module.table_prefix.value + "Per_Image"
            statement = ("select ImageNumber, Image_%s, Image_%s, Image_%s,"
                         "Image_Count_%s, %s "
                         "from %s" %
                         (INT_IMG_MEASUREMENT, FLOAT_IMG_MEASUREMENT,
                          STRING_IMG_MEASUREMENT, OBJECT_NAME,
                          wierd_img_column, image_table))
            self.cursor.execute(statement)
            row = self.cursor.fetchone()
            self.assertEqual(len(row), 6)
            self.assertEqual(row[0],1)
            self.assertAlmostEqual(row[1], INT_VALUE)
            self.assertAlmostEqual(row[2], FLOAT_VALUE)
            self.assertEqual(row[3], STRING_VALUE)
            self.assertEqual(row[4], len(OBJ_VALUE))
            self.assertEqual(row[5], 100)
            self.assertRaises(StopIteration, self.cursor.next)
            statement = ("select ImageNumber, ObjectNumber, %s_%s,%s "
                         "from %sPer_Object order by ObjectNumber"%
                         (OBJECT_NAME, OBJ_MEASUREMENT, wierd_obj_column,
                          module.table_prefix.value))
            self.cursor.execute(statement)
            for i, value in enumerate(OBJ_VALUE):
                row = self.cursor.fetchone()
                self.assertEqual(len(row), 4)
                self.assertEqual(row[0], 1)
                self.assertEqual(row[1], i+1)
                self.assertAlmostEqual(row[2], value)
                self.assertAlmostEqual(row[3], value)
            self.assertRaises(StopIteration, self.cursor.next)
        finally:
            for table_suffix in ("Per_Image","Per_Object"):
                table_name = module.table_prefix.value + table_suffix
                try:
                    self.cursor.execute("drop table %s.%s" %
                                        (module.db_name.value, table_name))
                except:
                    print "Failed to drop table %s"%table_name
                    
    def test_02_06_write_direct_50_char_colname(self):
        '''Write to MySQL, ensuring some columns have long names'''
        workspace, module = self.make_workspace(False, long_measurement=True)
        try:
            self.assertTrue(isinstance(module, E.ExportToDatabase))
            module.db_type = E.DB_MYSQL
            module.wants_agg_mean.value = False
            module.wants_agg_median.value = False
            module.wants_agg_std_dev.value = False
            module.objects_choice.value = E.O_ALL
            module.max_column_size.value = 50
            module.separate_object_tables.value = E.OT_COMBINE
            module.prepare_run(workspace.pipeline, workspace.image_set_list,None)
            module.prepare_group(workspace.pipeline, workspace.image_set_list,
                                 {}, [1])
            module.run(workspace)
            mappings = module.get_column_name_mappings(workspace.pipeline,
                                                       workspace.image_set_list)
            long_img_column = mappings["Image_%s"%LONG_IMG_MEASUREMENT]
            long_obj_column = mappings["%s_%s"%(OBJECT_NAME, LONG_OBJ_MEASUREMENT)]
            self.assertTrue(len(long_img_column) <= 50)
            self.assertTrue(len(long_obj_column) <= 50)
            self.cursor.execute("use CPUnitTest")
            #
            # Now read the image file from the database
            #
            image_table = module.table_prefix.value + "Per_Image"
            statement = ("select ImageNumber, Image_%s, Image_%s, Image_%s,"
                         "Image_Count_%s, %s "
                         "from %s" %
                         (INT_IMG_MEASUREMENT, FLOAT_IMG_MEASUREMENT,
                          STRING_IMG_MEASUREMENT, OBJECT_NAME,
                          long_img_column, image_table))
            self.cursor.execute(statement)
            row = self.cursor.fetchone()
            self.assertEqual(len(row), 6)
            self.assertEqual(row[0],1)
            self.assertAlmostEqual(row[1], INT_VALUE)
            self.assertAlmostEqual(row[2], FLOAT_VALUE)
            self.assertEqual(row[3], STRING_VALUE)
            self.assertEqual(row[4], len(OBJ_VALUE))
            self.assertEqual(row[5], 100)
            self.assertRaises(StopIteration, self.cursor.next)
            statement = ("select ImageNumber, ObjectNumber, %s_%s,%s "
                         "from %sPer_Object order by ObjectNumber"%
                         (OBJECT_NAME, OBJ_MEASUREMENT, long_obj_column,
                          module.table_prefix.value))
            self.cursor.execute(statement)
            for i, value in enumerate(OBJ_VALUE):
                row = self.cursor.fetchone()
                self.assertEqual(len(row), 4)
                self.assertEqual(row[0], 1)
                self.assertEqual(row[1], i+1)
                self.assertAlmostEqual(row[2], value)
                self.assertAlmostEqual(row[3], value)
            self.assertRaises(StopIteration, self.cursor.next)
        finally:
            for table_suffix in ("Per_Image","Per_Object"):
                table_name = module.table_prefix.value + table_suffix
                try:
                    self.cursor.execute("drop table %s.%s" %
                                        (module.db_name.value, table_name))
                except:
                    print "Failed to drop table %s"%table_name
                    
    def test_03_01_write_sqlite_direct(self):
        '''Write directly to a SQLite database'''
        workspace, module, output_dir, finally_fn = self.make_workspace(True)
        cursor = None
        connection = None
        try:
            self.assertTrue(isinstance(module, E.ExportToDatabase))
            module.db_type = E.DB_SQLITE
            module.wants_agg_mean.value = False
            module.wants_agg_median.value = False
            module.wants_agg_std_dev.value = False
            module.objects_choice.value = E.O_ALL
            module.directory_choice.value = E.DIR_CUSTOM
            module.output_directory.value = output_dir
            module.separate_object_tables.value = E.OT_COMBINE
            module.prepare_run(workspace.pipeline, workspace.image_set_list,None)
            module.prepare_group(workspace.pipeline, workspace.image_set_list,
                                 {}, [1])
            module.run(workspace)
            cursor, connection = self.get_sqlite_cursor(module)
            #
            # Now read the image file from the database
            #
            image_table = module.table_prefix.value + "Per_Image"
            statement = ("select ImageNumber, Image_%s, Image_%s, Image_%s, Image_Count_%s "
                         "from %s" %
                         (INT_IMG_MEASUREMENT, FLOAT_IMG_MEASUREMENT,
                          STRING_IMG_MEASUREMENT, OBJECT_NAME, image_table))
            cursor.execute(statement)
            row = cursor.fetchone()
            self.assertEqual(len(row), 5)
            self.assertEqual(row[0],1)
            self.assertAlmostEqual(row[1], INT_VALUE)
            self.assertAlmostEqual(row[2], FLOAT_VALUE)
            self.assertEqual(row[3], STRING_VALUE)
            self.assertEqual(row[4], len(OBJ_VALUE))
            self.assertRaises(StopIteration, cursor.next)
            statement = ("select ImageNumber, ObjectNumber, %s_%s "
                         "from %sPer_Object order by ObjectNumber"%
                         (OBJECT_NAME, OBJ_MEASUREMENT, module.table_prefix.value))
            cursor.execute(statement)
            for i, value in enumerate(OBJ_VALUE):
                row = cursor.fetchone()
                self.assertEqual(len(row), 3)
                self.assertEqual(row[0], 1)
                self.assertEqual(row[1], i+1)
                self.assertAlmostEqual(row[2], value)
            self.assertRaises(StopIteration, cursor.next)
        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None:
                connection.close()
            if hasattr(module, "cursor"):
                module.cursor.close()
            if hasattr(module, "connection"):
                module.connection.close()
            finally_fn()
            
    def test_04_01_stable_column_mapper(self):
        '''Make sure the column mapper always yields the same output'''
        mapping = E.ColumnNameMapping()
        k1 = 'abcdefghijkABCDEFGHIJABCDEFGHIJABCDEFGHIJABCDEFGHIJABCDEFGHIJABCDEFGHIJABC'
        k2 = 'ebcdefghijkABCDEFGHIJABCDEFGHIJABCDEFGHIJABCDEFGHIJABCDEFGHIJABCDEFGHIJABC'
        mapping.add(k1)
        mapping.add(k2)
        mapping.do_mapping()
        self.assertEqual(mapping[k1],'bABCDEFGHIJABCDEFGHIJABCDEFGHIJABCDEFGHIJABCDEFGHIJABCDEFGHIJABC')
        self.assertEqual(mapping[k2],'ebcdefghijkABCDFHIJABCDEFGHIJABCFGHIACDEFGHJABCDEFHIJABCDEFIJABC')
        
    def test_04_02_leave_start_intact(self):
        '''The column mapper should leave stuff before the first _ alone'''
        mapping = E.ColumnNameMapping(25)
        k1 = 'leaveme_EVEN_THOUGH_WE_LIKE_REMOVING_LOWER_CASE_VOWELS'
        k2 = 'keepmee_EVEN_THOUGH_WE_LIKE_REMOVING_LOWER_CASE_VOWELS'
        mapping.add(k1)
        mapping.add(k2)
        mapping.do_mapping()
        self.assertTrue(mapping[k1].startswith('leaveme_'))
        self.assertTrue(mapping[k2].startswith('keepmee_'))
        
    def per_object_statement(self, module, object_name, fields):
        '''Return a statement that will select the given fields from the table'''
        field_string = ", ".join([field if field.startswith(object_name)
                                  else "%s_%s" % (object_name, field)
                                  for field in fields])
        statement = ("select ImageNumber, %s_%s, %s "
                     "from %sPer_%s order by ImageNumber, %s_%s"%
                         (object_name, I.M_NUMBER_OBJECT_NUMBER, field_string, 
                          module.table_prefix.value, object_name, object_name,
                          I.M_NUMBER_OBJECT_NUMBER))
        return statement
        
    def test_05_01_write_mysql_db(self):
        '''Multiple objects / write - per-object tables'''
        workspace, module, output_dir, finally_fn = self.make_workspace(True)
        os.chdir(output_dir)
        try:
            self.assertTrue(isinstance(module, E.ExportToDatabase))
            module.db_type = E.DB_MYSQL_CSV
            module.wants_agg_mean.value = False
            module.wants_agg_median.value = False
            module.wants_agg_std_dev.value = False
            module.objects_choice.value = E.O_ALL
            module.directory_choice.value = E.DIR_CUSTOM
            module.output_directory.value = output_dir
            module.separate_object_tables.value = E.OT_PER_OBJECT
            module.post_run(workspace)
            sql_file = os.path.join(output_dir, "SQL__SETUP.SQL")
            base_name = "SQL_1_1"
            image_file = os.path.join(output_dir, base_name+"_image.CSV")
            object_file = os.path.join(output_dir, base_name+"_" + OBJECT_NAME + ".CSV")
            for filename in (sql_file, image_file, object_file):
                self.assertTrue(os.path.isfile(filename))
            fd = open(sql_file,'rt')
            sql_text = fd.read()
            fd.close()
            for statement in sql_text.split(';'):
                if len(statement.strip()) == 0:
                    continue
                self.cursor.execute(statement)
            #
            # Now read the image file from the database
            #
            image_table = module.table_prefix.value + "Per_Image"
            statement = ("select ImageNumber, Image_%s, Image_%s, Image_%s, Image_Count_%s "
                         "from %s" %
                         (INT_IMG_MEASUREMENT, FLOAT_IMG_MEASUREMENT,
                          STRING_IMG_MEASUREMENT, OBJECT_NAME, image_table))
            self.cursor.execute(statement)
            row = self.cursor.fetchone()
            self.assertEqual(len(row), 5)
            self.assertEqual(row[0],1)
            self.assertAlmostEqual(row[1], INT_VALUE)
            self.assertAlmostEqual(row[2], FLOAT_VALUE)
            self.assertEqual(row[3], STRING_VALUE)
            self.assertEqual(row[4], len(OBJ_VALUE))
            self.assertRaises(StopIteration, self.cursor.next)
            statement = self.per_object_statement(module, OBJECT_NAME,
                                                  [OBJ_MEASUREMENT])
            self.cursor.execute(statement)
            for i, value in enumerate(OBJ_VALUE):
                row = self.cursor.fetchone()
                self.assertEqual(len(row), 3)
                self.assertEqual(row[0], 1)
                self.assertEqual(row[1], i+1)
                self.assertAlmostEqual(row[2], value)
            self.assertRaises(StopIteration, self.cursor.next)
        finally:
            os.chdir(output_dir)
            finally_fn()
            for table_suffix in ("Per_Image","Per_%s" % OBJECT_NAME):
                table_name = module.table_prefix.value + table_suffix
                try:
                    self.cursor.execute("drop table %s.%s" %
                                        (module.db_name.value, table_name))
                except:
                    print "Failed to drop table %s"%table_name
    
    def test_05_02_write_mysql_db_filter_objs(self):
        workspace, module, output_dir, finally_fn = self.make_workspace(True, True)
        os.chdir(output_dir)
        try:
            self.assertTrue(isinstance(module, E.ExportToDatabase))
            module.db_type = E.DB_MYSQL_CSV
            module.wants_agg_mean.value = False
            module.wants_agg_median.value = False
            module.wants_agg_std_dev.value = False
            module.objects_choice.value = E.O_SELECT
            module.objects_list.choices = [OBJECT_NAME, ALTOBJECT_NAME]
            module.objects_list.value = OBJECT_NAME
            module.directory_choice.value = E.DIR_CUSTOM
            module.output_directory.value = output_dir
            module.separate_object_tables.value = E.OT_PER_OBJECT
            module.post_run(workspace)
            sql_file = os.path.join(output_dir, "SQL__SETUP.SQL")
            base_name = "SQL_1_1"
            image_file = os.path.join(output_dir, base_name+"_image.CSV")
            object_file = os.path.join(output_dir, base_name+"_" + OBJECT_NAME + ".CSV")
            for filename in (sql_file, image_file, object_file):
                self.assertTrue(os.path.isfile(filename))
            fd = open(sql_file,'rt')
            sql_text = fd.read()
            fd.close()
            for statement in sql_text.split(';'):
                if len(statement.strip()) == 0:
                    continue
                self.cursor.execute(statement)
            #
            # Now read the image file from the database
            #
            image_table = module.table_prefix.value + "Per_Image"
            statement = ("select ImageNumber, Image_%s, Image_%s, Image_%s, Image_Count_%s "
                         "from %s" %
                         (INT_IMG_MEASUREMENT, FLOAT_IMG_MEASUREMENT,
                          STRING_IMG_MEASUREMENT, OBJECT_NAME, image_table))
            self.cursor.execute(statement)
            row = self.cursor.fetchone()
            self.assertEqual(len(row), 5)
            self.assertEqual(row[0],1)
            self.assertAlmostEqual(row[1], INT_VALUE)
            self.assertAlmostEqual(row[2], FLOAT_VALUE)
            self.assertEqual(row[3], STRING_VALUE)
            self.assertEqual(row[4], len(OBJ_VALUE))
            self.assertRaises(StopIteration, self.cursor.next)
            statement = self.per_object_statement(module, OBJECT_NAME, 
                                                  [OBJ_MEASUREMENT])
            self.cursor.execute(statement)
            for i, value in enumerate(OBJ_VALUE):
                row = self.cursor.fetchone()
                self.assertEqual(len(row), 3)
                self.assertEqual(row[0], 1)
                self.assertEqual(row[1], i+1)
                self.assertAlmostEqual(row[2], value)
            self.assertRaises(StopIteration, self.cursor.next)
        finally:
            os.chdir(output_dir)
            finally_fn()
            for table_suffix in ("Per_Image","Per_%s" % OBJECT_NAME):
                table_name = module.table_prefix.value + table_suffix
                try:
                    self.cursor.execute("drop table %s.%s" %
                                        (module.db_name.value, table_name))
                except:
                    print "Failed to drop table %s"%table_name

    def test_05_03_mysql_direct(self):
        '''Write directly to the mysql DB, not to a file'''
        workspace, module = self.make_workspace(False)
        try:
            self.assertTrue(isinstance(module, E.ExportToDatabase))
            module.db_type = E.DB_MYSQL
            module.wants_agg_mean.value = False
            module.wants_agg_median.value = False
            module.wants_agg_std_dev.value = False
            module.objects_choice.value = E.O_ALL
            module.separate_object_tables.value = E.OT_PER_OBJECT
            module.prepare_run(workspace.pipeline, workspace.image_set_list,None)
            module.prepare_group(workspace.pipeline, workspace.image_set_list,
                                 {}, [1])
            module.run(workspace)
            self.cursor.execute("use CPUnitTest")
            #
            # Now read the image file from the database
            #
            image_table = module.table_prefix.value + "Per_Image"
            statement = ("select ImageNumber, Image_%s, Image_%s, Image_%s, Image_Count_%s "
                         "from %s" %
                         (INT_IMG_MEASUREMENT, FLOAT_IMG_MEASUREMENT,
                          STRING_IMG_MEASUREMENT, OBJECT_NAME, image_table))
            self.cursor.execute(statement)
            row = self.cursor.fetchone()
            self.assertEqual(len(row), 5)
            self.assertEqual(row[0],1)
            self.assertAlmostEqual(row[1], INT_VALUE)
            self.assertAlmostEqual(row[2], FLOAT_VALUE)
            self.assertEqual(row[3], STRING_VALUE)
            self.assertEqual(row[4], len(OBJ_VALUE))
            self.assertRaises(StopIteration, self.cursor.next)
            statement = self.per_object_statement(module, OBJECT_NAME, 
                                                  [OBJ_MEASUREMENT])
            self.cursor.execute(statement)
            for i, value in enumerate(OBJ_VALUE):
                row = self.cursor.fetchone()
                self.assertEqual(len(row), 3)
                self.assertEqual(row[0], 1)
                self.assertEqual(row[1], i+1)
                self.assertAlmostEqual(row[2], value)
            self.assertRaises(StopIteration, self.cursor.next)
        finally:
            for table_suffix in ("Per_Image","Per_%s" % OBJECT_NAME):
                table_name = module.table_prefix.value + table_suffix
                try:
                    self.cursor.execute("drop table %s.%s" %
                                        (module.db_name.value, table_name))
                except:
                    print "Failed to drop table %s"%table_name
    
    def test_05_04_write_direct_long_colname(self):
        '''Write to MySQL, ensuring some columns have long names'''
        workspace, module = self.make_workspace(False, long_measurement=True)
        try:
            self.assertTrue(isinstance(module, E.ExportToDatabase))
            module.db_type = E.DB_MYSQL
            module.wants_agg_mean.value = False
            module.wants_agg_median.value = False
            module.wants_agg_std_dev.value = False
            module.objects_choice.value = E.O_ALL
            module.separate_object_tables.value = E.OT_PER_OBJECT
            module.prepare_run(workspace.pipeline, workspace.image_set_list,None)
            module.prepare_group(workspace.pipeline, workspace.image_set_list,
                                 {}, [1])
            module.run(workspace)
            mappings = module.get_column_name_mappings(workspace.pipeline,
                                                       workspace.image_set_list)
            long_img_column = mappings["Image_%s"%LONG_IMG_MEASUREMENT]
            long_obj_column = mappings["%s_%s"%(OBJECT_NAME, LONG_OBJ_MEASUREMENT)]
            
            self.cursor.execute("use CPUnitTest")
            #
            # Now read the image file from the database
            #
            image_table = module.table_prefix.value + "Per_Image"
            statement = ("select ImageNumber, Image_%s, Image_%s, Image_%s,"
                         "Image_Count_%s, %s "
                         "from %s" %
                         (INT_IMG_MEASUREMENT, FLOAT_IMG_MEASUREMENT,
                          STRING_IMG_MEASUREMENT, OBJECT_NAME,
                          long_img_column, image_table))
            self.cursor.execute(statement)
            row = self.cursor.fetchone()
            self.assertEqual(len(row), 6)
            self.assertEqual(row[0],1)
            self.assertAlmostEqual(row[1], INT_VALUE)
            self.assertAlmostEqual(row[2], FLOAT_VALUE)
            self.assertEqual(row[3], STRING_VALUE)
            self.assertEqual(row[4], len(OBJ_VALUE))
            self.assertEqual(row[5], 100)
            self.assertRaises(StopIteration, self.cursor.next)
            statement = self.per_object_statement(module, OBJECT_NAME, 
                                                  [OBJ_MEASUREMENT, long_obj_column])
            self.cursor.execute(statement)
            for i, value in enumerate(OBJ_VALUE):
                row = self.cursor.fetchone()
                self.assertEqual(len(row), 4)
                self.assertEqual(row[0], 1)
                self.assertEqual(row[1], i+1)
                self.assertAlmostEqual(row[2], value)
                self.assertAlmostEqual(row[3], value)
            self.assertRaises(StopIteration, self.cursor.next)
        finally:
            for table_suffix in ("Per_Image","Per_%s" % OBJECT_NAME):
                table_name = module.table_prefix.value + table_suffix
                try:
                    self.cursor.execute("drop table %s.%s" %
                                        (module.db_name.value, table_name))
                except:
                    print "Failed to drop table %s"%table_name
        
    def test_05_05_write_nulls(self):
        workspace, module, output_dir, finally_fn = self.make_workspace(True)
        #
        # Insert a NaN into the float image measurement and one of the
        # object measurements
        #
        m = workspace.measurements
        fim = m.get_all_measurements(cpmeas.IMAGE, FLOAT_IMG_MEASUREMENT)
        fim[0] = np.NaN
        om = m.get_all_measurements(OBJECT_NAME, OBJ_MEASUREMENT)
        om[0][0] = np.NaN
        os.chdir(output_dir)
        try:
            self.assertTrue(isinstance(module, E.ExportToDatabase))
            module.db_type = E.DB_MYSQL_CSV
            module.wants_agg_mean.value = True
            module.wants_agg_median.value = False
            module.wants_agg_std_dev.value = False
            module.objects_choice.value = E.O_ALL
            module.directory_choice.value = E.DIR_CUSTOM
            module.output_directory.value = output_dir
            module.separate_object_tables.value = E.OT_PER_OBJECT
            module.post_run(workspace)
            sql_file = os.path.join(output_dir, "SQL__SETUP.SQL")
            base_name = "SQL_1_1"
            image_file = os.path.join(output_dir, base_name+"_image.CSV")
            object_file = os.path.join(output_dir, "%s_%s.CSV" %
                                       (base_name, OBJECT_NAME))
            for filename in (sql_file, image_file, object_file):
                self.assertTrue(os.path.isfile(filename))
            fd = open(sql_file,'rt')
            sql_text = fd.read()
            fd.close()
            for statement in sql_text.split(';'):
                if len(statement.strip()) == 0:
                    continue
                self.cursor.execute(statement)
            #
            # Now read the image file from the database
            #
            image_table = module.table_prefix.value + "Per_Image"
            statement = ("select ImageNumber, Image_%s, Image_%s, Image_%s, "
                         "Image_Count_%s, Mean_%s_%s "
                         "from %s" %
                         (INT_IMG_MEASUREMENT, FLOAT_IMG_MEASUREMENT,
                          STRING_IMG_MEASUREMENT, OBJECT_NAME, OBJECT_NAME,
                          OBJ_MEASUREMENT, image_table))
            self.cursor.execute(statement)
            row = self.cursor.fetchone()
            self.assertEqual(len(row), 6)
            self.assertEqual(row[0],1)
            self.assertAlmostEqual(row[1], INT_VALUE)
            self.assertTrue(row[2] is None)
            self.assertEqual(row[3], STRING_VALUE)
            self.assertEqual(row[4], len(OBJ_VALUE))
            self.assertAlmostEqual(row[5], np.mean(om[0][~np.isnan(om[0])]))
            self.assertRaises(StopIteration, self.cursor.next)
            statement = self.per_object_statement(module, OBJECT_NAME, 
                                                  [OBJ_MEASUREMENT])
            self.cursor.execute(statement)
            for i, value in enumerate(OBJ_VALUE):
                row = self.cursor.fetchone()
                self.assertEqual(len(row), 3)
                self.assertEqual(row[0], 1)
                self.assertEqual(row[1], i+1)
                if i == 0:
                    self.assertTrue(row[2] is None)
                else:
                    self.assertAlmostEqual(row[2], value)
            self.assertRaises(StopIteration, self.cursor.next)
        finally:
            os.chdir(output_dir)
            finally_fn()
            for table_suffix in ("Per_Image","Per_%s" % OBJECT_NAME):
                table_name = module.table_prefix.value + table_suffix
                try:
                    self.cursor.execute("drop table %s.%s" %
                                        (module.db_name.value, table_name))
                except:
                    print "Failed to drop table %s"%table_name
    
    def test_05_06_mysql_direct_null(self):
        '''Write directly to the mysql DB, not to a file and write nulls'''
        workspace, module = self.make_workspace(False)
        #
        # Insert a NaN into the float image measurement and one of the
        # object measurements
        #
        m = workspace.measurements
        fim = m.get_all_measurements(cpmeas.IMAGE, FLOAT_IMG_MEASUREMENT)
        fim[0] = np.NaN
        om = m.get_all_measurements(OBJECT_NAME, OBJ_MEASUREMENT)
        om[0][:] = np.NaN
        try:
            self.assertTrue(isinstance(module, E.ExportToDatabase))
            module.db_type = E.DB_MYSQL
            module.wants_agg_mean.value = True
            module.wants_agg_median.value = False
            module.wants_agg_std_dev.value = False
            module.objects_choice.value = E.O_ALL
            module.separate_object_tables.value = E.OT_PER_OBJECT
            module.prepare_run(workspace.pipeline, workspace.image_set_list,None)
            module.prepare_group(workspace.pipeline, workspace.image_set_list,
                                 {}, [1])
            module.run(workspace)
            self.cursor.execute("use CPUnitTest")
            #
            # Now read the image file from the database
            #
            image_table = module.table_prefix.value + "Per_Image"
            statement = ("select ImageNumber, Image_%s, Image_%s, Image_%s, "
                         "Image_Count_%s, Mean_%s_%s "
                         "from %s" %
                         (INT_IMG_MEASUREMENT, FLOAT_IMG_MEASUREMENT,
                          STRING_IMG_MEASUREMENT, OBJECT_NAME,
                          OBJECT_NAME, OBJ_MEASUREMENT, image_table))
            self.cursor.execute(statement)
            row = self.cursor.fetchone()
            self.assertEqual(len(row), 6)
            self.assertEqual(row[0],1)
            self.assertAlmostEqual(row[1], INT_VALUE)
            self.assertTrue(row[2] is None)
            self.assertEqual(row[3], STRING_VALUE)
            self.assertEqual(row[4], len(OBJ_VALUE))
            self.assertTrue(row[5] is None)
            self.assertRaises(StopIteration, self.cursor.next)
            statement = self.per_object_statement(module, OBJECT_NAME, 
                                                  [OBJ_MEASUREMENT])
            self.cursor.execute(statement)
            for i, value in enumerate(OBJ_VALUE):
                row = self.cursor.fetchone()
                self.assertEqual(len(row), 3)
                self.assertEqual(row[0], 1)
                self.assertEqual(row[1], i+1)
                self.assertTrue(row[2] is None)
            self.assertRaises(StopIteration, self.cursor.next)
        finally:
            for table_suffix in ("Per_Image","Per_%s" % OBJECT_NAME):
                table_name = module.table_prefix.value + table_suffix
                try:
                    self.cursor.execute("drop table %s.%s" %
                                        (module.db_name.value, table_name))
                except:
                    print "Failed to drop table %s"%table_name
                    
    def test_05_07_write_direct_wierd_colname(self):
        '''Write to MySQL, even if illegal characters are in the column name'''
        workspace, module = self.make_workspace(False, wierd_measurement=True)
        try:
            self.assertTrue(isinstance(module, E.ExportToDatabase))
            module.db_type = E.DB_MYSQL
            module.wants_agg_mean.value = False
            module.wants_agg_median.value = False
            module.wants_agg_std_dev.value = False
            module.objects_choice.value = E.O_ALL
            module.separate_object_tables.value = E.OT_PER_OBJECT
            module.prepare_run(workspace.pipeline, workspace.image_set_list,None)
            module.prepare_group(workspace.pipeline, workspace.image_set_list,
                                 {}, [1])
            module.run(workspace)
            mappings = module.get_column_name_mappings(workspace.pipeline,
                                                       workspace.image_set_list)
            wierd_img_column = mappings["Image_%s"%WIERD_IMG_MEASUREMENT]
            wierd_obj_column = mappings["%s_%s"%(OBJECT_NAME, WIERD_OBJ_MEASUREMENT)]
            
            self.cursor.execute("use CPUnitTest")
            #
            # Now read the image file from the database
            #
            image_table = module.table_prefix.value + "Per_Image"
            statement = ("select ImageNumber, Image_%s, Image_%s, Image_%s,"
                         "Image_Count_%s, %s "
                         "from %s" %
                         (INT_IMG_MEASUREMENT, FLOAT_IMG_MEASUREMENT,
                          STRING_IMG_MEASUREMENT, OBJECT_NAME,
                          wierd_img_column, image_table))
            self.cursor.execute(statement)
            row = self.cursor.fetchone()
            self.assertEqual(len(row), 6)
            self.assertEqual(row[0],1)
            self.assertAlmostEqual(row[1], INT_VALUE)
            self.assertAlmostEqual(row[2], FLOAT_VALUE)
            self.assertEqual(row[3], STRING_VALUE)
            self.assertEqual(row[4], len(OBJ_VALUE))
            self.assertEqual(row[5], 100)
            self.assertRaises(StopIteration, self.cursor.next)
            statement = self.per_object_statement(
                module, OBJECT_NAME, [OBJ_MEASUREMENT, wierd_obj_column])
            self.cursor.execute(statement)
            for i, value in enumerate(OBJ_VALUE):
                row = self.cursor.fetchone()
                self.assertEqual(len(row), 4)
                self.assertEqual(row[0], 1)
                self.assertEqual(row[1], i+1)
                self.assertAlmostEqual(row[2], value)
                self.assertAlmostEqual(row[3], value)
            self.assertRaises(StopIteration, self.cursor.next)
        finally:
            for table_suffix in ("Per_Image","Per_%s" % OBJECT_NAME):
                table_name = module.table_prefix.value + table_suffix
                try:
                    self.cursor.execute("drop table %s.%s" %
                                        (module.db_name.value, table_name))
                except:
                    print "Failed to drop table %s"%table_name
                    
    def test_05_07_write_direct_50_char_colname(self):
        '''Write to MySQL, ensuring some columns have long names'''
        workspace, module = self.make_workspace(False, long_measurement=True)
        try:
            self.assertTrue(isinstance(module, E.ExportToDatabase))
            module.db_type = E.DB_MYSQL
            module.wants_agg_mean.value = False
            module.wants_agg_median.value = False
            module.wants_agg_std_dev.value = False
            module.objects_choice.value = E.O_ALL
            module.max_column_size.value = 50
            module.separate_object_tables.value = E.OT_PER_OBJECT
            module.prepare_run(workspace.pipeline, workspace.image_set_list,None)
            module.prepare_group(workspace.pipeline, workspace.image_set_list,
                                 {}, [1])
            module.run(workspace)
            mappings = module.get_column_name_mappings(workspace.pipeline,
                                                       workspace.image_set_list)
            long_img_column = mappings["Image_%s"%LONG_IMG_MEASUREMENT]
            long_obj_column = mappings["%s_%s"%(OBJECT_NAME, LONG_OBJ_MEASUREMENT)]
            self.assertTrue(len(long_img_column) <= 50)
            self.assertTrue(len(long_obj_column) <= 50)
            self.cursor.execute("use CPUnitTest")
            #
            # Now read the image file from the database
            #
            image_table = module.table_prefix.value + "Per_Image"
            statement = ("select ImageNumber, Image_%s, Image_%s, Image_%s,"
                         "Image_Count_%s, %s "
                         "from %s" %
                         (INT_IMG_MEASUREMENT, FLOAT_IMG_MEASUREMENT,
                          STRING_IMG_MEASUREMENT, OBJECT_NAME,
                          long_img_column, image_table))
            self.cursor.execute(statement)
            row = self.cursor.fetchone()
            self.assertEqual(len(row), 6)
            self.assertEqual(row[0],1)
            self.assertAlmostEqual(row[1], INT_VALUE)
            self.assertAlmostEqual(row[2], FLOAT_VALUE)
            self.assertEqual(row[3], STRING_VALUE)
            self.assertEqual(row[4], len(OBJ_VALUE))
            self.assertEqual(row[5], 100)
            self.assertRaises(StopIteration, self.cursor.next)
            statement = self.per_object_statement(module, OBJECT_NAME, 
                                                  [OBJ_MEASUREMENT, long_obj_column])
            self.cursor.execute(statement)
            for i, value in enumerate(OBJ_VALUE):
                row = self.cursor.fetchone()
                self.assertEqual(len(row), 4)
                self.assertEqual(row[0], 1)
                self.assertEqual(row[1], i+1)
                self.assertAlmostEqual(row[2], value)
                self.assertAlmostEqual(row[3], value)
            self.assertRaises(StopIteration, self.cursor.next)
        finally:
            for table_suffix in ("Per_Image","Per_%s" % OBJECT_NAME):
                table_name = module.table_prefix.value + table_suffix
                try:
                    self.cursor.execute("drop table %s.%s" %
                                        (module.db_name.value, table_name))
                except:
                    print "Failed to drop table %s"%table_name
                    
    def test_05_08_write_two_object_tables_direct(self):
        '''Write two object tables using OT_PER_OBJECT'''
        workspace, module = self.make_workspace(
            False, alt_object = True)
        try:
            self.assertTrue(isinstance(module, E.ExportToDatabase))
            module.db_type = E.DB_MYSQL
            module.wants_agg_mean.value = False
            module.wants_agg_median.value = False
            module.wants_agg_std_dev.value = False
            module.objects_choice.value = E.O_ALL
            module.max_column_size.value = 50
            module.separate_object_tables.value = E.OT_PER_OBJECT
            module.prepare_run(workspace.pipeline, workspace.image_set_list,None)
            module.prepare_group(workspace.pipeline, workspace.image_set_list,
                                 {}, [1])
            module.run(workspace)
            #
            # Read from one object table
            #
            self.cursor.execute("use CPUnitTest")
            statement = self.per_object_statement(module, OBJECT_NAME, 
                                                  [OBJ_MEASUREMENT])
            self.cursor.execute(statement)
            for i, value in enumerate(OBJ_VALUE):
                row = self.cursor.fetchone()
                self.assertEqual(len(row), 3)
                self.assertEqual(row[0], 1)
                self.assertEqual(row[1], i+1)
                self.assertAlmostEqual(row[2], value)
            self.assertRaises(StopIteration, self.cursor.next)
            #
            # Read from the other table
            #
            statement = self.per_object_statement(module, ALTOBJECT_NAME, 
                                                  [OBJ_MEASUREMENT])
            self.cursor.execute(statement)
            for i in range(100):
                row = self.cursor.fetchone()
                self.assertEqual(len(row), 3)
                self.assertEqual(row[0], 1)
                self.assertEqual(row[1], i+1)
                self.assertAlmostEqual(row[2], i)
            self.assertRaises(StopIteration, self.cursor.next)
        finally:
            for table_suffix in ("Per_Image","Per_%s" % OBJECT_NAME):
                table_name = module.table_prefix.value + table_suffix
                try:
                    self.cursor.execute("drop table %s.%s" %
                                        (module.db_name.value, table_name))
                except:
                    print "Failed to drop table %s"%table_name
                    
    def test_06_01_write_sqlite_direct(self):
        '''Write directly to a SQLite database'''
        workspace, module, output_dir, finally_fn = self.make_workspace(True)
        cursor = None
        connection = None
        try:
            self.assertTrue(isinstance(module, E.ExportToDatabase))
            module.db_type = E.DB_SQLITE
            module.wants_agg_mean.value = False
            module.wants_agg_median.value = False
            module.wants_agg_std_dev.value = False
            module.objects_choice.value = E.O_ALL
            module.directory_choice.value = E.DIR_CUSTOM
            module.output_directory.value = output_dir
            module.separate_object_tables.value = E.OT_PER_OBJECT
            module.prepare_run(workspace.pipeline, workspace.image_set_list,None)
            module.prepare_group(workspace.pipeline, workspace.image_set_list,
                                 {}, [1])
            module.run(workspace)
            cursor, connection = self.get_sqlite_cursor(module)
            #
            # Now read the image file from the database
            #
            image_table = module.table_prefix.value + "Per_Image"
            statement = ("select ImageNumber, Image_%s, Image_%s, Image_%s, Image_Count_%s "
                         "from %s" %
                         (INT_IMG_MEASUREMENT, FLOAT_IMG_MEASUREMENT,
                          STRING_IMG_MEASUREMENT, OBJECT_NAME, image_table))
            cursor.execute(statement)
            row = cursor.fetchone()
            self.assertEqual(len(row), 5)
            self.assertEqual(row[0],1)
            self.assertAlmostEqual(row[1], INT_VALUE)
            self.assertAlmostEqual(row[2], FLOAT_VALUE)
            self.assertEqual(row[3], STRING_VALUE)
            self.assertEqual(row[4], len(OBJ_VALUE))
            self.assertRaises(StopIteration, cursor.next)
            statement = self.per_object_statement(module, OBJECT_NAME,
                                                  [OBJ_MEASUREMENT])
            cursor.execute(statement)
            for i, value in enumerate(OBJ_VALUE):
                row = cursor.fetchone()
                self.assertEqual(len(row), 3)
                self.assertEqual(row[0], 1)
                self.assertEqual(row[1], i+1)
                self.assertAlmostEqual(row[2], value)
            self.assertRaises(StopIteration, cursor.next)
        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None:
                connection.close()
            if hasattr(module, "cursor"):
                module.cursor.close()
            if hasattr(module, "connection"):
                module.connection.close()
            finally_fn()
    
    def execute_well_sql(self, output_dir, module):
        file_name = "SQL__Per_Well_SETUP.SQL"
        sql_file = os.path.join(output_dir, file_name)
        fd = open(sql_file,'rt')
        sql_text = fd.read()
        fd.close()
        print sql_text
        for statement in sql_text.split(';'):
            if len(statement.strip()) == 0:
                continue
            self.cursor.execute(statement)
        
    def select_well_agg(self, module, aggname, fields):
        field_string = ", ".join(["%s_%s" % (aggname, field)
                                  for field in fields])
        statement = ("select Image_Metadata_Plate, Image_Metadata_Well, %s "
                     "from %sPer_Well_%s" % 
                     (field_string, module.table_prefix.value, aggname))
        return statement
        
    def test_07_01_well_single_objtable(self):
        workspace, module, output_dir, finally_fn = self.make_workspace(
            False, well_metadata = True)
        try:
            self.assertTrue(isinstance(module, E.ExportToDatabase))
            module.db_type = E.DB_MYSQL
            module.wants_agg_mean.value = False
            module.wants_agg_median.value = False
            module.wants_agg_std_dev.value = False
            module.objects_choice.value = E.O_ALL
            module.max_column_size.value = 50
            module.separate_object_tables.value = E.OT_PER_OBJECT
            module.wants_agg_mean_well.value = True
            module.wants_agg_median_well.value = True
            module.wants_agg_std_dev_well.value = True
            module.prepare_run(workspace.pipeline, workspace.image_set_list,None)
            module.prepare_group(workspace.pipeline, workspace.image_set_list,
                                 {}, [1])
            module.run(workspace)
            module.post_run(workspace)
            self.execute_well_sql(output_dir, module)
            meas = ((cpmeas.IMAGE, FLOAT_IMG_MEASUREMENT),
                    (cpmeas.IMAGE, INT_IMG_MEASUREMENT),
                    (OBJECT_NAME, OBJ_MEASUREMENT))
            for aggname, aggfn in (("avg", np.mean),
                                   ("median", np.median),
                                   ("std", np.std)):
                fields = ["%s_%s" % (object_name, feature)
                          for object_name, feature in meas]
                statement = self.select_well_agg(module, aggname, fields)
                self.cursor.execute(statement)
                rows = self.cursor.fetchall()
                self.assertEqual(len(rows), 1)
                row = rows[0]
                self.assertEqual(row[0], PLATE)
                self.assertEqual(row[1], WELL)
                for i, (object_name, feature) in enumerate(meas):
                    value = row[i+2]
                    values = workspace.measurements.get_current_measurement(object_name, feature)
                    expected = aggfn(values)
                    if np.isnan(expected):
                        self.assertTrue(value is None)
                    else:
                        self.assertAlmostEqual(float(value), expected)
        finally:
            for table_suffix in ("Per_Image","Per_%s" % OBJECT_NAME, "Per_Well"):
                table_name = module.table_prefix.value + table_suffix
                try:
                    self.cursor.execute("drop table %s.%s" %
                                        (module.db_name.value, table_name))
                except:
                    print "Failed to drop table %s"%table_name
            finally_fn()
            
    def test_07_02_well_two_objtables(self):
        workspace, module, output_dir, finally_fn = self.make_workspace(
            False, well_metadata = True, alt_object = True)
        try:
            self.assertTrue(isinstance(module, E.ExportToDatabase))
            module.db_type = E.DB_MYSQL
            module.wants_agg_mean.value = False
            module.wants_agg_median.value = False
            module.wants_agg_std_dev.value = False
            module.objects_choice.value = E.O_ALL
            module.max_column_size.value = 50
            module.separate_object_tables.value = E.OT_PER_OBJECT
            module.wants_agg_mean_well.value = True
            module.wants_agg_median_well.value = True
            module.wants_agg_std_dev_well.value = True
            module.prepare_run(workspace.pipeline, workspace.image_set_list,None)
            module.prepare_group(workspace.pipeline, workspace.image_set_list,
                                 {}, [1])
            module.run(workspace)
            module.post_run(workspace)
            self.execute_well_sql(output_dir, module)
            meas = ((cpmeas.IMAGE, FLOAT_IMG_MEASUREMENT),
                    (cpmeas.IMAGE, INT_IMG_MEASUREMENT),
                    (OBJECT_NAME, OBJ_MEASUREMENT),
                    (ALTOBJECT_NAME, OBJ_MEASUREMENT))
            for aggname, aggfn in (("avg", np.mean),
                                   ("median", np.median),
                                   ("std", np.std)):
                fields = ["%s_%s" % (object_name, feature)
                          for object_name, feature in meas]
                statement = self.select_well_agg(module, aggname, fields)
                self.cursor.execute(statement)
                rows = self.cursor.fetchall()
                self.assertEqual(len(rows), 1)
                row = rows[0]
                self.assertEqual(row[0], PLATE)
                self.assertEqual(row[1], WELL)
                for i, (object_name, feature) in enumerate(meas):
                    value = row[i+2]
                    values = workspace.measurements.get_current_measurement(object_name, feature)
                    expected = aggfn(values)
                    if np.isnan(expected):
                        self.assertTrue(value is None)
                    else:
                        self.assertAlmostEqual(float(value), expected)
        finally:
            for table_suffix in ("Per_Image", "Per_%s" % OBJECT_NAME, 
                                 "Per_%s" % ALTOBJECT_NAME, "Per_Well"):
                table_name = module.table_prefix.value + table_suffix
                try:
                    self.cursor.execute("drop table %s.%s" %
                                        (module.db_name.value, table_name))
                except:
                    print "Failed to drop table %s"%table_name
            finally_fn()            