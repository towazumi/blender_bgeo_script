from collections import OrderedDict

class StringList:
    """ 文字列のリストを名前とインデックスで管理するリスト """

    def __init__(self):
        self.string_list = list()
        self.index_list = list()

    def append(self, string):
        if string is None or len(string)==0:
            self.index_list.append(-1)
            return

        string = self.remove_space(string)

        if string in self.string_list:
            self.index_list.append( self.string_list.index(string) )
        else:
            index = len(self.string_list)
            self.string_list.append(string)
            self.index_list.append(index)

    def index(self, string):
        if string is None or len(string)==0:
            return -1

        string = self.remove_space(string)

        if string in self.string_list:
            str_index = self.string_list.index( string )
            return self.index_list.index(str_index)
        return -1

    def remove_space(self, string):
        return string.replace(" ", "_")

class CurvePrimInfo:
    """ カーブの情報をまとめたもの """
    def __init__(self):
        self.type = "BezierCurve" # or "NURBCurve"
        self.vertices = list()
        self.closed = False
        self.basis = "Bezier" # or "NURBS"
        self.knots = [0.0, 0.5, 1.0]
        self.order = 4
        self.endinterpolation = None # NURBSの時にbool値を設定 


class PackedGeoInfo:
    """ PackedGeometryの情報をまとめたもの """
    def __init__(self):
        self.embed_id = ""
        self.bgeo = None
        self.type = None
        self.name = None
        self.position = [0.0, 0.0, 0.0]
        self.bounds = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.pivot = [0.0, 0.0, 0.0]
        self.transform = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]


class GeometryAttribute:
    """ GeometryのAttribute一つを表すもの """

    def __init__(self):
        self.type = "numeric" # or "string" / "indexpair" / "stringarray" / "arraydata"
        self.name = None
        self.options = None # "point" / "normal" / "texturecoord" /  "indexpair" / "matrix"
        self.values = list()

    @staticmethod
    def point():
        attrib = GeometryAttribute() 
        attrib.type = "numeric"
        attrib.name = "P"
        attrib.options = "point"
        return attrib

    @staticmethod
    def normal():
        attrib = GeometryAttribute() 
        attrib.type = "numeric"
        attrib.name = "N"
        attrib.options = "normal"
        return attrib

    @staticmethod
    def color(name):
        attrib = GeometryAttribute() 
        attrib.type = "numeric"
        attrib.name = name
        attrib.options = "color"
        return attrib

    @staticmethod
    def texturecoord(name):
        attrib = GeometryAttribute() 
        attrib.type = "numeric"
        attrib.name = name
        attrib.options = "texturecoord"
        return attrib

    @staticmethod
    def numeric(name):
        attrib = GeometryAttribute() 
        attrib.type = "numeric"
        attrib.name = name
        return attrib

    @staticmethod
    def matrix(name):
        attrib = GeometryAttribute() 
        attrib.type = "numeric"
        attrib.name = name
        attrib.options = "matrix"
        return attrib

    @staticmethod
    def string(name):
        attrib = GeometryAttribute() 
        attrib.type = "string"
        attrib.name = name
        attrib.options = "string"
        attrib.values = StringList()
        return attrib

class EdgeGroup:
    """ エッジグループ """

    def __init__(self):
        self.name  = ""
        self.points = list()


class GeometryInfo:
    """ ジオメトリ出力のために必要な情報をまとめたもの """

    GEO_FILE_VER = "20.5.410"

    def __init__(self):

        # point
        self.point_attributes = list()

        # vertex
        self.vertex_attributes = list()
        
        # primitive
        self.primitive_attributes = list()

        # edge group
        self.edge_groups = list()

        # p_r:Polygon_Run c_r:PolygonCurve_Run
        self.primitive_type = "p_r"
        
        self.loop_counts = list()
        self.indices = list()

        self.curves = list()

    def find_point_attributes(self, name):
        for attrib in self.point_attributes:
            if attrib.name == name:
                return attrib
        return None

    def find_vertex_attributes(self, name):
        for attrib in self.vertex_attributes:
            if attrib.name == name:
                return attrib
        return None

    def find_primitive_attributes(self, name):
        for attrib in self.primitive_attributes:
            if attrib.name == name:
                return attrib
        return None


    def point_count(self):
        """ HoudiniでのPoint数 """
        return len(self.point_attributes[0].values) if len( self.point_attributes )>0 else 0

    def vertex_count(self):
        """ HoudiniでのVertex数 """
        return len( self.indices )

    def primitive_count(self):
        """ HoudiniでのPrimitive数 """
        return len( self.loop_counts ) + len(self.curves)

    def nvertices_rle(self):
        """ 頂点数、その頂点数のポリゴン数を並べた配列 """
        rle = list()
        count = 0
        nvertices = 0
        for loop_count in self.loop_counts:
            if nvertices != loop_count and count>0:
                rle.append(nvertices)
                rle.append(count)
                count = 0

            nvertices = loop_count
            count += 1

        if nvertices>0 and count>0:
            rle.append(nvertices)
            rle.append(count)

        return rle