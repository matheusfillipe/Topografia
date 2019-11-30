from collada import material, Collada, geometry, scene, source
def test():
        filename="test.dae"
        mesh = Collada()
        effect = material.Effect("effect0", [], "phong", diffuse=(1, 0, 0), specular=(0, 1,0))
        mat = material.Material("material0", "mymaterial", effect)
        mesh.effects.append(effect)
        mesh.materials.append(mat)

        import numpy
        vert_floats = [-50, 50, 50, 50, 50, 50, -50, -50, 50, 50,
                       -50, 50, -50, 50, -50, 50, 50, -50, -50, -50, -50, 50, -50, -50]
        normal_floats = [0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1,0,
                         0, 1, 0, 0, 1, 0, 0, 1, 0, 0, -1, 0, 0, -1, 0, 0, -1, 0, 0, -1, 0, -1, 0, 0,
                         -1, 0, 0, -1, 0, 0, -1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, -1,
                         0, 0, -1, 0, 0, -1, 0, 0, -1]
        vert_src = source.FloatSource("cubeverts-array", numpy.array(vert_floats), ('X','Y', 'Z'))
        normal_src = source.FloatSource("cubenormals-array", numpy.array(normal_floats), ('X', 'Y', 'Z'))
        geom = geometry.Geometry(mesh, "geometry0", "mycube", [vert_src, normal_src])
        input_list = source.InputList()
        input_list.addInput(0, 'VERTEX', "#cubeverts-array")
        input_list.addInput(1, 'NORMAL', "#cubenormals-array")
        indices = numpy.array([0, 0, 2, 1, 3, 2, 0, 0, 3, 2, 1, 3, 0, 4, 1, 5, 5, 6, 0,
                               4, 5, 6, 4, 7, 6, 8, 7, 9, 3, 10, 6, 8, 3, 10, 2, 11, 0, 12,
                               4, 13, 6, 14, 0, 12, 6, 14, 2, 15, 3, 16, 7, 17, 5, 18, 3,
                               16, 5, 18, 1, 19, 5, 20, 7, 21, 6, 22, 5, 20, 6, 22, 4, 23])
        triset = geom.createTriangleSet(indices, input_list, "materialref")
        geom.primitives.append(triset)
        mesh.geometries.append(geom)
        matnode = scene.MaterialNode("materialref", mat, inputs=[])
        geomnode = scene.GeometryNode(geom, [matnode])
        node = scene.Node("node0", children=[geomnode])
        myscene = scene.Scene("myscene", [node])
        mesh.scenes.append(myscene)
        mesh.scene = myscene
        mesh.write(filename)

test()
