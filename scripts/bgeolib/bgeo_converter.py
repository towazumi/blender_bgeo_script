import itertools

from .bgeo_writer import BinaryJsonWriter
from .geo_info import StringList
from .geo_info import GeometryInfo

GEO_FILE_VER = GeometryInfo.GEO_FILE_VER

class BgeoConverter:
    """ GeometryInfoからbgeoデータに変換 """

    class MeshWriter(BinaryJsonWriter):

        def __init__(self):
            super().__init__()

        def attrib_info(self, geo_attrib):
            with self.array_block():
                self.write_attribute_info("public", geo_attrib.type, geo_attrib.name)
                self.write_attribute_options(geo_attrib.options)

        def float_attrib_values(self, values):
            with self.array_block():
                self.write_attribute_size_storage(1, "fpreal32")

                self.write_idstring("defaults")
                with self.array_block():

                    self.write_attribute_size_storage(1, "fpreal64")

                    self.write_idstring("values")
                    self.write_fpreal64_uniform_array([0.0,])

                self.write_idstring("values")
                with self.array_block():
                    self.write_attribute_size_storage(1, "fpreal32")

                    self.write_idstring("pagesize")
                    self.write_int(1024)

                    self.write_idstring("rawpagedata")
                    self.write_fpreal32_uniform_array( values )

        def vector2_attrib_values(self, values):
            with self.array_block():
                self.write_attribute_size_storage(2, "fpreal32")

                self.write_idstring("defaults")
                with self.array_block():

                    self.write_attribute_size_storage(1, "fpreal64")

                    self.write_idstring("values")
                    self.write_fpreal64_uniform_array([0.0,])

                self.write_idstring("values")
                with self.array_block():
                    self.write_attribute_size_storage(2, "fpreal32")

                    self.write_idstring("pagesize")
                    self.write_int(1024)

                    self.write_idstring("rawpagedata")
                    self.write_fpreal32_uniform_array( list( itertools.chain.from_iterable(values) ) )

        def vector3_attrib_values(self, values):
            with self.array_block():
                self.write_attribute_size_storage(3, "fpreal32")

                self.write_idstring("defaults")
                with self.array_block():

                    self.write_attribute_size_storage(1, "fpreal64")

                    self.write_idstring("values")
                    self.write_fpreal64_uniform_array([0.0,])

                self.write_idstring("values")
                with self.array_block():
                    self.write_attribute_size_storage(3, "fpreal32")

                    self.write_idstring("pagesize")
                    self.write_int(1024)

                    self.write_idstring("rawpagedata")
                    self.write_fpreal32_uniform_array( list( itertools.chain.from_iterable(values) ) )

        def transform_attrib_values(self, values):
            with self.array_block():
                self.write_attribute_size_storage(9, "fpreal32")

                self.write_idstring("defaults")
                with self.array_block():

                    self.write_attribute_size_storage(1, "fpreal64")

                    self.write_idstring("values")
                    self.write_fpreal64_uniform_array([0.0,])

                self.write_idstring("values")
                with self.array_block():
                    self.write_attribute_size_storage(9, "fpreal32")

                    self.write_idstring("pagesize")
                    self.write_int(1024)

                    self.write_idstring("rawpagedata")
                    self.write_fpreal32_uniform_array( list( itertools.chain.from_iterable(values) ) )

        def bonecapture_attrib_values(self, bone_names, bone_matrices, weights):

            pagesize = 1024

            # boneCapture_pCaptData
            captdata = [ list() for i in range(0, 20) ]
            for matrix in bone_matrices:
                for i in range(0, 16):
                    captdata[i].append( matrix[i%4][i//4] ) # transpose 
                captdata[16].append(1.0)
                captdata[17].append(1.0)
                captdata[18].append(1.0)
                captdata[19].append(1.0)

            # boneのinfluence数の最大値を調べる 
            # weightsはbone_index, weightのリストのリスト  
            point_count = len(weights)
            max_influence_count = 0
            for point_weight in weights:
                max_influence_count = max( max_influence_count, len(point_weight)//2 )

            bone_indices = [-1] * point_count * max_influence_count
            
            # ページごとにデータをパックする 
            page_num = (point_count + pagesize - 1) // pagesize
            for pagei in range(0, page_num):
                inputi = pagei * pagesize
                page_offset = max_influence_count * inputi
                num_page_elements = min(pagesize, point_count-inputi)
                for i in range(0, num_page_elements):
                    point_weight = weights[inputi + i]
                    weight_count = len(point_weight)//2
                    for wi in range(0, weight_count):
                        bone_indices[page_offset + wi*num_page_elements + i ] = point_weight[2*wi]

            bone_weights = list()
            for i in range(0, max_influence_count):
                bone_weight_data = list()
                for point_weight in weights:
                    if (2*i+1) < len(point_weight):
                        bone_weight_data.append(point_weight[ 2*i + 1 ])
                    else:
                        bone_weight_data.append(-1.0)
                bone_weights.append(bone_weight_data)


            with self.array_block():
                self.write_idstring("idefault")
                with self.array_block():
                    self.write_attribute_size_storage(1, "int64")

                    self.write_idstring("values")
                    self.write_int64_uniform_array([-1,])

                self.write_idstring("vdefault")
                with self.array_block():
                    self.write_attribute_size_storage(1, "fpreal64")

                    self.write_idstring("values")
                    self.write_fpreal64_uniform_array([-1.0,])

                self.write_idstring("objectsets")
                with self.array_block():
                    with self.array_block():

                        self.write_idstring("entries")
                        self.write_int(len(bone_names))

                        self.write_idstring("properties")
                        with self.array_block():
                            with self.array_block():

                                self.write_idstring("name")
                                self.write_string("pCaptPath")

                                self.write_idstring("storage")
                                self.write_idstring("string")

                                self.write_idstring("size")
                                self.write_int(1)

                                self.write_idstring("defaults")
                                with self.array_block():
                                    self.write_string("")

                                self.write_idstring("value")
                                with self.array_block():
                                    with self.array_block():
                                        for bone_name in bone_names:
                                            self.write_string(bone_name)

                            with self.array_block():

                                self.write_idstring("name")
                                self.write_string("pCaptData")

                                self.write_idstring("storage")
                                self.write_idstring("fpreal32")

                                self.write_idstring("size")
                                self.write_int(20)

                                self.write_idstring("defaults")
                                with self.array_block():
                                    self.write_real32(1.0)
                                    self.write_real32(0.0)
                                    self.write_real32(0.0)
                                    self.write_real32(0.0)

                                    self.write_real32(0.0)
                                    self.write_real32(1.0)
                                    self.write_real32(0.0)
                                    self.write_real32(0.0)

                                    self.write_real32(0.0)
                                    self.write_real32(0.0)
                                    self.write_real32(1.0)
                                    self.write_real32(0.0)

                                    self.write_real32(0.0)
                                    self.write_real32(0.0)
                                    self.write_real32(0.0)
                                    self.write_real32(1.0)

                                    self.write_real32(1.0)
                                    self.write_real32(1.0)
                                    self.write_real32(1.0)
                                    self.write_real32(1.0)

                                self.write_idstring("value")
                                with self.array_block():
                                    for data in captdata:
                                        self.write_fpreal32_uniform_array(data)

                self.write_idstring("istorage")
                self.write_idstring("int32")

                self.write_idstring("vsize")
                self.write_int(1)

                self.write_idstring("vstorage")
                self.write_idstring("fpreal32")

                self.write_idstring("entries")
                self.write_int(max_influence_count)

                self.write_idstring("index")
                with self.array_block():
                    self.write_attribute_size_storage(max_influence_count, "int32")

                    self.write_idstring("pagesize")
                    self.write_int(pagesize)
                    
                    self.write_idstring("packing")
                    self.write_uint8_uniform_array([1]*max_influence_count)
                    
                    self.write_idstring("rawpagedata")
                    self.write_int32_uniform_array(bone_indices)

                self.write_idstring("value")
                with self.array_block():
                    for bone_weight in bone_weights:
                        with self.array_block():
                            self.write_attribute_size_storage(1, "fpreal32")

                            self.write_idstring("pagesize")
                            self.write_int(1024)

                            self.write_idstring("rawpagedata")
                            self.write_fpreal32_uniform_array(bone_weight)

        
        def string_attrib_values(self, name_list, name_indices):
            with self.array_block():
                self.write_attribute_size_storage(1, "int32")
                self.write_idstring("strings")
                with self.array_block():
                    for name in name_list:
                        self.write_idstring(name)

                self.write_idstring("indices")
                with self.array_block():
                    self.write_attribute_size_storage(1, "int32")

                    self.write_idstring("pagesize")
                    self.write_int(1024)

                    self.write_idstring("rawpagedata")
                    self.write_int32_uniform_array(name_indices)

        def attrib_values(self, geo_attrib):

            if geo_attrib.type=="string":
                self.string_attrib_values(geo_attrib.values.string_list, geo_attrib.values.index_list)
            else:
                if isinstance(geo_attrib.values[0], float):
                    self.float_attrib_values(geo_attrib.values)
                elif len(geo_attrib.values[0])==2:
                    self.vector2_attrib_values(geo_attrib.values)
                elif len(geo_attrib.values[0])==3:
                    self.vector3_attrib_values(geo_attrib.values)
                elif len(geo_attrib.values[0])==9:
                    self.transform_attrib_values(geo_attrib.values)
                else:
                    raise NotImplementedError()


        def global_capt_name_values(self, bone_names):
            with self.array_block():
                self.write_attribute_size_storage(1, "int32")
                self.write_idstring("strings")
                with self.array_block():
                    for name in bone_names:
                        self.write_idstring(name)

                self.write_idstring("indices")
                with self.array_block():
                    self.write_int32_uniform_array([ i for i in range(0, len(bone_names))])
        

        def global_capt_parents_values(self, bone_parents):
            with self.array_block():
                self.write_attribute_size_storage(1, "int32")
                
                self.write_idstring("values")
                with self.array_block():
                    self.write_int32_uniform_array(bone_parents)
        

        def global_capt_xforms_values(self, bone_matrices):

            float_arrays = list()
            for matrix in bone_matrices:
                for i in range(0, 16):
                    float_arrays.append( matrix[i%4][i//4] ) # transpose 

            with self.array_block():
                self.write_attribute_size_storage(16, "fpreal32")

                self.write_idstring("values")
                with self.array_block():
                    self.write_fpreal32_uniform_array(float_arrays)


    def __init__(self):
        pass

    def convert(self, geo_info):
        writer = BgeoConverter.MeshWriter()

        hasindex = False

        with writer.array_block():

            writer.write_idstring("fileversion")
            writer.write_idstring(GEO_FILE_VER)

            writer.write_idstring("hasindex")
            writer.write_bool(hasindex)

            writer.write_idstring("pointcount")
            writer.write_int(geo_info.point_count())

            writer.write_idstring("vertexcount")
            writer.write_int(geo_info.vertex_count())

            writer.write_idstring("primitivecount")
            writer.write_int(geo_info.primitive_count())

            writer.write_idstring("info")
            with writer.map_block():
                writer.write_idstring("software")
                writer.write_idstring("Blender Houdini Geometry Exporter")

            writer.write_idstring("topology")
            with writer.array_block():

                writer.write_idstring("pointref")
                with writer.array_block():

                    writer.write_idstring("indices")
                    writer.write_auto_int_uniform_array( geo_info.indices )


            writer.write_idstring("attributes")
            with writer.array_block():

                if len(geo_info.vertex_attributes)>0:
                    writer.write_idstring("vertexattributes")
                    with writer.array_block():
                        
                        for attrib in geo_info.vertex_attributes:
                            with writer.array_block():
                                writer.attrib_info(attrib)
                                writer.attrib_values(attrib)


                if len(geo_info.point_attributes)>0:
                    writer.write_idstring("pointattributes")
                    with writer.array_block():

                        for attrib in geo_info.point_attributes:
                            with writer.array_block():
                                writer.attrib_info(attrib)
                                writer.attrib_values(attrib)


                if len(geo_info.primitive_attributes)>0:
                    writer.write_idstring("primitiveattributes")
                    with writer.array_block():

                        for attrib in geo_info.primitive_attributes:
                            with writer.array_block():
                                writer.attrib_info(attrib)
                                writer.attrib_values(attrib)
      

            writer.write_idstring("primitives")
            with writer.array_block():
                # メッシュ 
                if len(geo_info.loop_counts)>0:
                    with writer.array_block():
                        with writer.array_block():
                            writer.write_idstring("type")
                            writer.write_idstring(geo_info.primitive_type)
                        with writer.array_block():
                            writer.write_idstring("s_v") # startvertex
                            writer.write_int(0)
                            writer.write_idstring("n_p") # nprimitives
                            writer.write_int(geo_info.primitive_count())
                            writer.write_idstring("r_v") # nvertices_rle
                            writer.write_auto_int_uniform_array(geo_info.nvertices_rle())
                # カーブ 
                for curve in geo_info.curves:
                    with writer.array_block():
                        with writer.array_block():
                            writer.write_idstring("type")
                            writer.write_idstring(curve.type)
                        with writer.array_block():
                            writer.write_idstring("vertex")
                            writer.write_int16_uniform_array(curve.vertices)
                            writer.write_idstring("closed")
                            writer.write_bool(curve.closed)
                            writer.write_idstring("basis")
                            with writer.array_block():
                                writer.write_idstring("type")
                                writer.write_idstring(curve.basis)
                                writer.write_idstring("order")
                                writer.write_int(curve.order)
                                if curve.endinterpolation is not None:
                                    writer.write_idstring("endinterpolation")
                                    writer.write_bool(curve.endinterpolation)
                                writer.write_idstring("knots")
                                writer.write_fpreal64_uniform_array(curve.knots)


            if len(geo_info.edge_groups)>0:
                writer.write_idstring("edgegroups")
                with writer.array_block():

                    for edge_group in geo_info.edge_groups:
                        with writer.array_block():

                            with writer.array_block():
                                writer.write_idstring("name")
                                writer.write_idstring(edge_group.name)
                                
                            with writer.array_block():
                                writer.write_idstring("points")
                                with writer.array_block():
                                    for i in edge_group.points:
                                        writer.write_int(i)

            if hasindex: # 詳細不明だけどなくても動く
                writer.write_string("index")
                with writer.array_block():
                    writer.write_string("integerentries")
                    with writer.map_block():
                        pass
                    writer.write_string("stringentries")
                    with writer.map_block():
                        pass
                    writer.write_string("integerkeyentries")
                    with writer.map_block():
                        pass
                    writer.write_string("stringkeyentries")
                    with writer.map_block():
                        pass
                writer.write_string("indexposition")
                writer.write_int64(102)

        return writer.getvalue()

    def pack(self, packed_geo_list):
        writer = BgeoConverter.MeshWriter()

        hasindex = False

        type_list = StringList()
        name_list = StringList()

        for packed_geo in packed_geo_list:
            type_list.append(packed_geo.type)
            name_list.append(packed_geo.name)

        with writer.array_block():

            writer.write_idstring("fileversion")
            writer.write_idstring(GEO_FILE_VER)

            writer.write_idstring("hasindex")
            writer.write_bool(hasindex)

            writer.write_idstring("pointcount")
            writer.write_int(len(packed_geo_list))

            writer.write_idstring("vertexcount")
            writer.write_int(len(packed_geo_list))

            writer.write_idstring("primitivecount")
            writer.write_int(len(packed_geo_list))

            writer.write_idstring("info")
            with writer.map_block():
                writer.write_idstring("software")
                writer.write_idstring("Blender Houdini Geometry Exporter")

            writer.write_idstring("topology")
            with writer.array_block():

                writer.write_idstring("pointref")
                with writer.array_block():

                    indices = list(range(0, len(packed_geo_list)))
                    writer.write_idstring("indices")
                    writer.write_auto_int_uniform_array( indices )

            writer.write_idstring("attributes")
            with writer.array_block():

                writer.write_idstring("pointattributes")
                with writer.array_block():

                    with writer.array_block():
                        with writer.array_block():
                            writer.write_attribute_info("public", "numeric", "P")
                            writer.write_attribute_options("point")
                        writer.vector3_attrib_values( [g.position for g in packed_geo_list] )

                writer.write_idstring("primitiveattributes")
                with writer.array_block():

                    with writer.array_block():
                        with writer.array_block():
                            writer.write_attribute_info("public", "string", "type")
                            writer.write_attribute_options(None)
                        writer.string_attrib_values(type_list.string_list, type_list.index_list)

                    with writer.array_block():
                        with writer.array_block():
                            writer.write_attribute_info("public", "string", "name")
                            writer.write_attribute_options(None)
                        writer.string_attrib_values(name_list.string_list, name_list.index_list)


            writer.write_idstring("primitives")
            with writer.array_block():

                for i, packed_geo in enumerate(packed_geo_list):

                    with writer.array_block():
                        with writer.array_block():
                            writer.write_idstring("type")
                            writer.write_idstring("PackedGeometry")
                        with writer.array_block():
                            writer.write_idstring("parameters")
                            with writer.map_block():
                                # writer.write_idstring("cachedbounds")
                                # writer.write_fpreal64_uniform_array(packed_geo.bounds)
                                writer.write_idstring("embedded")
                                writer.write_idstring("embed:" + packed_geo.embed_id)
                                writer.write_idstring("pointinstancetransform")
                                writer.write_int(0)
                                writer.write_idstring("treatasfolder")
                                writer.write_int(0)
                            writer.write_idstring("pivot")
                            writer.write_fpreal32_uniform_array(packed_geo.pivot)
                            writer.write_idstring("transform")
                            writer.write_fpreal64_uniform_array(packed_geo.transform)
                            writer.write_idstring("vertex")
                            writer.write_int(i)
                            writer.write_idstring("viewportlod")
                            writer.write_idstring("full")

            writer.write_idstring("sharedprimitivedata")
            with writer.array_block():

                for packed_geo in packed_geo_list:
                    bytes_array = "PackedGeometry".encode('utf-8')
                    writer.io.write(b'+') # 0x2b
                    writer.write_length( 0 )
                    writer.write_length( len(bytes_array) )
                    writer.io.write(bytes_array)
                    writer.io.write(b'&') # 0x26
                    writer.write_length( 0 )

                    with writer.array_block():
                        writer.write_string("gu:embeddedgeo")
                        writer.write_string("embed:"+packed_geo.embed_id)
                        writer.io.write(packed_geo.bgeo[5:])

        return writer.getvalue()
                        