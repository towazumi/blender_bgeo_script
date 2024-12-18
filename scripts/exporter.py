
# "C:\Program Files\Blender Foundation\Blender 4.3\blender.exe" --background test.blend --python script.py

import bpy
from bpy_extras.io_utils import axis_conversion
from mathutils import Matrix

import numpy as np

import os
import sys

sys.path.append(os.path.dirname(__file__))
from bgeolib.geo_info import CurvePrimInfo
from bgeolib.geo_info import PackedGeoInfo
from bgeolib.geo_info import GeometryAttribute
from bgeolib.geo_info import EdgeGroup
from bgeolib.geo_info import GeometryInfo
from bgeolib.bgeo_converter import BgeoConverter

def get_outliner_path(ob):
    """ アウトライナーでのパスを取得 """

    def get_parent_collection(ob):
        for collection in bpy.data.collections:
            for obj in collection.objects:
                if ob == obj:
                    return collection
            for child in collection.children:
                if child == ob:
                    return collection
        
        return None


    root_collection = bpy.context.scene.collection
    path = ob.name
    
    search_target = ob
    parent = ob.parent
    
    while parent:
        path = parent.name + "/" + path
        search_target = parent
        parent = parent.parent

    collection = get_parent_collection(search_target)
    while collection and collection!=root_collection:
        path = collection.name + "/" + path
        collection = get_parent_collection(collection)

    return path

def get_mesh_from_object(ob):
    """ オブジェクトからメッシュを取得 """
    try:
        me = ob.to_mesh()
    except RuntimeError:
        me = None

    return me

def convert_bezier_curve(geo, spline, axis_conv_matrix):
    """ ベジェカーブの情報をGeometryInfoに変換 """

    index_offset = geo.point_count()

    point_list = list()
    radius_list = list()
    tilt_list = list()

    closed = spline.use_cyclic_u

    for p in spline.bezier_points:
        handle_left = axis_conv_matrix @ p.handle_left
        co = axis_conv_matrix @ p.co
        handle_right = axis_conv_matrix @ p.handle_right

        point_list.extend([handle_left[:], co[:], handle_right[:]])
        radius_list.extend([p.radius, p.radius, p.radius])
        tilt_list.extend([p.tilt, p.tilt, p.tilt])
    
    p_attrib = geo.find_point_attributes("P")
    if p_attrib is None:
        p_attrib = GeometryAttribute.point()
        geo.point_attributes.append(p_attrib)

    if closed:
        point_list = point_list[1:] + point_list[:1]
        radius_list = radius_list[1:] + radius_list[:1]
        tilt_list = tilt_list[1:] + tilt_list[:1]
    else:
        point_list = point_list[1:-1]
        radius_list = radius_list[1:-1]
        tilt_list = tilt_list[1:-1]

    p_attrib.values.extend( point_list )

    radius_attrib = geo.find_point_attributes("radius")
    if radius_attrib is None:
        radius_attrib = GeometryAttribute.numeric("radius")
        geo.point_attributes.append(radius_attrib)
    radius_attrib.values.extend( radius_list )
    
    tilt_attrib = geo.find_point_attributes("tilt")
    if tilt_attrib is None:
        tilt_attrib = GeometryAttribute.numeric("tilt")
        geo.point_attributes.append(tilt_attrib)
    tilt_attrib.values.extend( tilt_list )

    point_count = len(point_list)
    ctr_point_count = len(spline.bezier_points)+1 if closed else len(spline.bezier_points)

    geo.indices.extend( [ i+index_offset for i in range(0, point_count) ] )

    curve_info = CurvePrimInfo()
    curve_info.type = "BezierCurve"
    curve_info.vertices.extend( [ i+index_offset for i in range(0, point_count) ] )
    curve_info.closed = spline.use_cyclic_u
    curve_info.basis = "Bezier"
    curve_info.knots = [ float(i) / (ctr_point_count-1) for i in range(0, ctr_point_count) ]
    curve_info.order = 4 # 固定 

    geo.curves.append(curve_info)

def convert_nurbs_bezier_curve(geo, spline, axis_conv_matrix):
    """ Bezierにチェックの入ったNURBSカーブの情報をGeometryInfoに変換 """

    index_offset = geo.point_count()

    point_list = list()
    radius_list = list()
    tilt_list = list()

    closed = spline.use_cyclic_u

    for p in spline.points:
        co = axis_conv_matrix @ p.co
        point_list.append(co[:3])
        radius_list.append(p.radius)
        tilt_list.append(p.tilt)

    point_count = len(point_list)

    if closed:
        if point_count%(spline.order_u-1)!=0:
            return
        ctr_point_count = point_count // (spline.order_u-1) + 1
        
    else:
        if (point_count-1)%(spline.order_u-1)!=0:
            return
        ctr_point_count = (point_count-1) // (spline.order_u-1)

    p_attrib = geo.find_point_attributes("P")
    if p_attrib is None:
        p_attrib = GeometryAttribute.point()
        geo.point_attributes.append(p_attrib)
    p_attrib.values.extend( point_list )

    radius_attrib = geo.find_point_attributes("radius")
    if radius_attrib is None:
        radius_attrib = GeometryAttribute.numeric("radius")
        geo.point_attributes.append(radius_attrib)
    radius_attrib.values.extend( radius_list )
    
    tilt_attrib = geo.find_point_attributes("tilt")
    if tilt_attrib is None:
        tilt_attrib = GeometryAttribute.numeric("tilt")
        geo.point_attributes.append(tilt_attrib)
    tilt_attrib.values.extend( tilt_list )

    geo.indices.extend( [ i+index_offset for i in range(0, point_count) ] )


    curve_info = CurvePrimInfo()
    curve_info.type = "BezierCurve"
    curve_info.vertices.extend( [ i+index_offset for i in range(0, point_count) ] )
    curve_info.closed = spline.use_cyclic_u
    curve_info.basis = "Bezier"
    curve_info.knots = [ float(i) / (ctr_point_count-1) for i in range(0, ctr_point_count) ]
    curve_info.order = spline.order_u

    geo.curves.append(curve_info)


def convert_nurbs_curve(geo, spline, axis_conv_matrix):
    """ NURBSカーブの情報をGeometryInfoに変換 """

    index_offset = geo.point_count()
    point_list = list()
    radius_list = list()
    tilt_list = list()

    for p in spline.points:
        co = axis_conv_matrix @ p.co
        point_list.append(co[:3])
        radius_list.append(p.radius)
        tilt_list.append(p.tilt)

    p_attrib = geo.find_point_attributes("P")
    if p_attrib is None:
        p_attrib = GeometryAttribute.point()
        geo.point_attributes.append(p_attrib)
    p_attrib.values.extend( point_list )

    radius_attrib = geo.find_point_attributes("radius")
    if radius_attrib is None:
        radius_attrib = GeometryAttribute.numeric("radius")
        geo.point_attributes.append(radius_attrib)
    radius_attrib.values.extend( radius_list )
    
    tilt_attrib = geo.find_point_attributes("tilt")
    if tilt_attrib is None:
        tilt_attrib = GeometryAttribute.numeric("tilt")
        geo.point_attributes.append(tilt_attrib)
    tilt_attrib.values.extend( tilt_list )

    
    point_count = len(point_list)
    knots_count = max(point_count + spline.order_u, 2*spline.order_u)
    if spline.use_cyclic_u:
        knots_count += 1
    geo.indices.extend( [ i+index_offset for i in range(0, point_count) ] )

    knots = list()
    for i in range(0, spline.order_u):
        knots.append(0.0)
    for i in range(0, max(0, knots_count-2*spline.order_u)):
        knots.append( (i+1.0) /(knots_count-2*spline.order_u+1) )
    while len(knots)<knots_count:
        knots.append(1.0)

    curve_info = CurvePrimInfo()
    curve_info.type = "NURBCurve"
    curve_info.vertices.extend( [ i+index_offset for i in range(0, point_count) ] )
    curve_info.closed = spline.use_cyclic_u
    curve_info.basis = "NURBS"
    curve_info.knots = knots
    curve_info.order = spline.order_u
    curve_info.endinterpolation = spline.use_endpoint_u

    geo.curves.append(curve_info)


def convert_curve(obj, axis_conv_matrix):
    """ CURVEをbgeoに変換 """
    geo = GeometryInfo()

    for s in obj.data.splines:
        if s.type=="BEZIER":
            convert_bezier_curve(geo, s, axis_conv_matrix)
        elif s.type=="NURBS":
            if s.use_bezier_u:
                convert_nurbs_bezier_curve(geo, s, axis_conv_matrix)
            else:
                convert_nurbs_curve(geo, s, axis_conv_matrix)

    if len(geo.curves)==0:
        return None
            
    converter = BgeoConverter()
    return converter.convert(geo)

def convet_armature(obj, axis_conv_matrix):
    """ ARMATURE """

    geo = GeometryInfo()
    geo.primitive_type = "c_r"

    # 骨の向き調整用の行列 
    bone_correction_matrix = axis_conversion(
        from_forward="Y",
        from_up="X",
        to_forward="Y",
        to_up="X",
        ).to_3x3()

    armature = obj

    p_attrib = GeometryAttribute.point() 
    name_attrib = GeometryAttribute.string("name")
    transform_attrib = GeometryAttribute.matrix("transform")
    length_attrib = GeometryAttribute.numeric("length") 


    for i, bone in enumerate(armature.pose.bones):
        translation = bone.matrix.to_translation()
        bone_matrix = axis_conv_matrix @ Matrix.Translation(translation) @ ( (bone.matrix.to_3x3() @ bone_correction_matrix).to_4x4() )
            
        position = bone_matrix.to_translation()[:]
        transform_values = [ bone_matrix[i%3][i//3] for i in range(0, 9)]

        if bone.parent is not None:
            index = name_attrib.values.index(bone.parent.name)
            geo.indices.append(index)
            geo.indices.append(i)
            geo.loop_counts.append(2)

        p_attrib.values.append( position )
        name_attrib.values.append(bone.name)
        transform_attrib.values.append(transform_values)
        length_attrib.values.append(bone.length)

    geo.point_attributes.append(p_attrib)
    geo.point_attributes.append(name_attrib)
    geo.point_attributes.append(transform_attrib)
    geo.point_attributes.append(length_attrib)

    converter = BgeoConverter()
    return converter.convert(geo)


def convert_mesh(obj, axis_conv_matrix):
    """ メッシュとしてbgeoに変換 """

    geo = GeometryInfo()

    # modifierを適用 
    depsgraph = bpy.context.evaluated_depsgraph_get()  
    eval_ob = obj.evaluated_get(depsgraph)
    me = get_mesh_from_object(eval_ob)
    if me is None:
        return None

    me.transform(axis_conv_matrix)
    
    # P
    p_attrib = GeometryAttribute.point() 
    p_attrib.values = [ v.co[:] for v in me.vertices]

    geo.point_attributes.append(p_attrib)

    # vertex_group
    vg_attribs = list()
    for group in obj.vertex_groups:
        vg_attrib = GeometryAttribute.numeric(group.name) 
        vg_attrib.values = np.zeros(geo.point_count())
        vg_attribs.append(vg_attrib)

    for i, v in enumerate(me.vertices):
        for g in v.groups:
            vg_attribs[g.group].values[i] = g.weight

    geo.point_attributes.extend(vg_attribs)
    
    n_attrib = GeometryAttribute.normal()
    uv_attribs = [ GeometryAttribute.texturecoord(uv_layer.name) for uv_layer in me.uv_layers ]
    material_name_attrib = GeometryAttribute.string("material_name") 

    materials = me.materials[:]
    for polygon in me.polygons:
        loop_start = polygon.loop_start
        loop_total = polygon.loop_total
        # 面の向きを逆に
        loop_indices = list()
        if loop_total>0:
            loop_indices.append(loop_start)
        for i in range(loop_total-1, 0, -1):
            loop_indices.append(loop_start+i)

        for loop_index in loop_indices:
            loop = me.loops[loop_index]

            geo.indices.append(loop.vertex_index)
            n_attrib.values.append(loop.normal[:])

            for i, uv_layer in enumerate(me.uv_layers):
                uv = uv_layer.data[loop_index].uv[:] if uv_layer.data else [ 0.0, 0.0 ]
                uv_attribs[i].values.append( [ uv[0], uv[1], 0.0 ] )

        geo.loop_counts.append(loop_total)

        # material 
        material = materials[polygon.material_index] if 0<=polygon.material_index and polygon.material_index<len(materials) else None 
        material_name = material.name if material is not None else None

        material_name_attrib.values.append(material_name)

    geo.vertex_attributes.extend(uv_attribs)
    if len(n_attrib.values)>0:
        geo.vertex_attributes.append(n_attrib)

    if len(material_name_attrib.values.string_list)>0:
        geo.primitive_attributes.append(material_name_attrib)

    # Color Attribute 
    # print(me.color_attributes)
    for color_attribute in me.color_attributes:
        color_attrib = GeometryAttribute.color(color_attribute.name)
        color_attrib.values = [ d.color[:3] for d in color_attribute.data ]
        # color_attrib.values = [ d.color_srgb[:3] for d in color_attribute.data ]
        if color_attribute.domain=="POINT":
            geo.point_attributes.append(color_attrib)
        elif color_attribute.domain=="CORNER":
            geo.vertex_attributes.append(color_attrib)

    # Edge group
    seams_edges = [ edge for edge in me.edges if edge.use_seam ]
    if len(seams_edges)>0:
        seams_group = EdgeGroup()
        seams_group.name = "seams"
        for edge in seams_edges:
            seams_group.points.extend(edge.vertices)
        geo.edge_groups.append(seams_group)
    
    sharp_edges = [ edge for edge in me.edges if edge.use_edge_sharp ]
    if len(sharp_edges)>0:
        sharp_group = EdgeGroup()
        sharp_group.name = "sharp"
        for edge in sharp_edges:
            sharp_group.points.extend(edge.vertices)
        geo.edge_groups.append(sharp_group)


    eval_ob.to_mesh_clear()

    if geo.primitive_count()==0:
        return None

    converter = BgeoConverter()
    return converter.convert(geo)


def convert_mesh_shapekey(obj, axis_conv_matrix):
    """ メッシュとしてbgeoに変換(ブレンドシェイプ用に最小構成) """

    geo = GeometryInfo()

    # modifierを適用 
    depsgraph = bpy.context.evaluated_depsgraph_get()  
    eval_ob = obj.evaluated_get(depsgraph)
    me = get_mesh_from_object(eval_ob)
    if me is None:
        return None

    me.transform(axis_conv_matrix)
    
    # P
    p_attrib = GeometryAttribute.point() 
    p_attrib.values = [ v.co[:] for v in me.vertices]
    geo.point_attributes.append(p_attrib)

    n_attrib = GeometryAttribute.normal()
    
    for polygon in me.polygons:
        loop_start = polygon.loop_start
        loop_total = polygon.loop_total
        # 面の向きを逆に
        loop_indices = list()
        if loop_total>0:
            loop_indices.append(loop_start)
        for i in range(loop_total-1, 0, -1):
            loop_indices.append(loop_start+i)

        for loop_index in loop_indices:
            loop = me.loops[loop_index]

            geo.indices.append(loop.vertex_index)
            n_attrib.values.append(loop.normal[:])

        geo.loop_counts.append(loop_total)

    geo.vertex_attributes.append(n_attrib)

    eval_ob.to_mesh_clear()

    if geo.primitive_count()==0:
        return None

    converter = BgeoConverter()
    return converter.convert(geo)    

def convert(obj, axis_conv_matrix, for_shape_key):
    if obj.type in ("CAMERA", "LIGHT", "EMPTY"):
        return None
    elif obj.type == "CURVE":
        return convert_curve(obj, axis_conv_matrix)
    elif obj.type == "ARMATURE":
        return convet_armature(obj, axis_conv_matrix)
    elif for_shape_key:
        return convert_mesh_shapekey(obj, axis_conv_matrix)
    else:
        return convert_mesh(obj, axis_conv_matrix)


def save_bgeosc_file(data, path):
    import struct
    from bgeolib.blosc_compression_filter import BloscCompressionFilter

    if BloscCompressionFilter.blosc is None:
        raise Exception("blosc.dll is not loaded.")

    with open(path, "wb") as f:
        # header
        f.write(b"scf1")
        f.write(b"\0"*8) # metadata 
        
        # compressed bgeo data 
        sc_filter = BloscCompressionFilter()
        sc_filter.write( f, data )
        sc_filter.close( f )
        
        # index 
        sc_filter.index.write_to_stream(f)
        # footer
        f.write( struct.pack(">Q", sc_filter.index.length()) )
        f.write(b"1fcs")



if __name__=="__main__":

    argv = sys.argv

    if "--" not in argv:
        raise RuntimeError("export bgeo required. add \"--\" \"[bgeo path]\"")
        
    argv = argv[argv.index("--") + 1:]
    if len(argv)<1:
        raise RuntimeError("export bgeo required. add \"--\" \"[bgeo path]\"")

    export_path = argv[0]
    
    # activeがあればオブジェクトモードにする
    if bpy.context.view_layer.objects.active is not None:
        bpy.ops.object.mode_set(mode = "OBJECT")

    # Armatureのポーズをリセット 
    for obj in bpy.context.scene.objects:
        if obj.type == "ARMATURE":
            for pose_bone in obj.pose.bones:
                pose_bone.matrix_basis.identity()


    packed_geo_list = list()
    embed_id = 1

    # BlenderのZ-upをY-upに変換する行列 
    axis_conv_matrix = axis_conversion(
        from_forward="-Y", from_up="Z", 
        to_forward="Z",to_up="Y",).to_4x4()


    for obj in bpy.context.scene.objects:

        bgeo_list = list() # name, type, bgeoのリスト 
        name = get_outliner_path(obj) 

        if hasattr(obj.data, "shape_keys") and obj.data.shape_keys is not None:

            # shape keyを一旦すべてクリア 
            for shape_key in obj.data.shape_keys.key_blocks:
                shape_key.value = 0.0
            
            # shape keyを有効にしながらすべて回す 
            for i, shape_key in enumerate(obj.data.shape_keys.key_blocks):
                shape_key.value = 1.0

                bgeo = convert(obj, axis_conv_matrix, i>0) # 0番目以外は最小情報で出力されるように 
                if bgeo is not None:
                    bgeo_list.append( (name+"." + shape_key.name, obj.type, bgeo) )

                # curveだったらMeshに変換可能かテスト 
                if obj.type == "CURVE":
                    bgeo = convert_mesh(obj, axis_conv_matrix)
                    if bgeo is not None:
                        bgeo_list.append( (name+"." + shape_key.name, "MESH", bgeo) )

                shape_key.value = 0.0

        else:
            bgeo = convert(obj, axis_conv_matrix, False)
            if bgeo is not None:
                bgeo_list.append( (name, obj.type, bgeo) )

            # curveだったらMeshに変換可能かテスト 
            if obj.type == "CURVE":
                bgeo = convert_mesh(obj, axis_conv_matrix)
                if bgeo is not None:
                    bgeo_list.append( (name, "MESH", bgeo) )

        for name, obj_type, bgeo in bgeo_list:
            
            # 確認用に個別でbgeo出力 
            # filepath = os.path.join(os.path.dirname(__file__), "..", "geo", name+".bgeo")
            # dirname = os.path.dirname(filepath)
            # os.makedirs(dirname, exist_ok=True)
            # with open(filepath, "wb") as f:
            #     f.write(bgeo)

            loc, rot, scale = obj.matrix_world.decompose()
            loc.y, loc.z = loc.z, -loc.y
            rot.y, rot.z = rot.z, -rot.y
            scale.y, scale.z = scale.z, scale.y
            matrix = Matrix.LocRotScale(loc, rot, scale)

            packed_geo = PackedGeoInfo()
            packed_geo.embed_id = "{:016x}".format(embed_id)
            packed_geo.bgeo = bgeo
            packed_geo.type = obj_type
            packed_geo.name = name
            packed_geo.position = loc[:]
            packed_geo.transform = [ matrix[i%3][i//3] for i in range(0, 9)]
            packed_geo_list.append(packed_geo)

            embed_id += 1


    # PackedGeometryにまとめる 
    converter = BgeoConverter()
    packed_data = converter.pack(packed_geo_list)

    # bgeo出力 
    export_dir = os.path.dirname(export_path)
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)

    if export_path.endswith(".bgeo.sc"):
        save_bgeosc_file(packed_data, export_path)
    else:
        with open(export_path, "wb") as f:
            f.write(packed_data)


