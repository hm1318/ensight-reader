import mmap
import os.path as op
import tempfile

import numpy as np

from ensight2obj import ensight2obj
from ensight2vtk import ensight2vtk
from ensightreader import ElementType, EnsightGeometryFile, GeometryPart, IdHandling, read_case

ENSIGHT_CASE_PATH = "./data/sphere/sphere.case"


def test_read_sphere_case():
    # check casefile
    case = read_case(ENSIGHT_CASE_PATH)

    assert case.get_variables() == ["RTData"]
    assert case.get_node_variables() == ["RTData"]
    assert case.get_element_variables() == []

    assert not case.is_transient()
    assert case.get_time_values() is None

    # check geofile
    geofile = case.get_geometry_model()
    assert isinstance(geofile, EnsightGeometryFile)

    assert geofile.description_line1.startswith("Written by VTK EnSight Writer")
    assert geofile.description_line2.startswith("No Title was Specified")
    assert geofile.node_id_handling == IdHandling.GIVEN
    assert geofile.element_id_handling == IdHandling.GIVEN
    assert geofile.extents is None

    assert geofile.get_part_names() == ["VTK Part"]
    part = geofile.get_part_by_name("VTK Part")
    assert isinstance(part, GeometryPart)
    assert part.part_name == "VTK Part"
    assert geofile.parts[part.part_id] is part
    assert part.part_id == 1
    assert part.number_of_nodes == 50
    assert part.number_of_elements == 96

    with open(geofile.file_path, "rb") as fp_geo:
        nodes = part.read_nodes(fp_geo)
        assert nodes.shape == NODES_REF.shape
        assert nodes.dtype == NODES_REF.dtype
        assert np.allclose(nodes, NODES_REF)
        assert nodes.flags.writeable

        node_ids = part.read_node_ids(fp_geo)
        assert node_ids.shape == NODE_IDS_REF.shape
        assert node_ids.dtype == NODE_IDS_REF.dtype
        assert np.equal(node_ids, NODE_IDS_REF).all()
        assert node_ids.flags.writeable

        assert len(part.element_blocks) == 1
        block = part.element_blocks[0]
        assert block.element_type == ElementType.TRIA3
        connectivity = block.read_connectivity(fp_geo)
        assert connectivity.shape == (96, 3)
        assert connectivity.dtype == np.int32
        assert connectivity.flags.writeable

        element_ids = block.read_element_ids(fp_geo)
        assert element_ids.shape == ELEMENT_IDS_REF.shape
        assert element_ids.dtype == ELEMENT_IDS_REF.dtype
        assert np.equal(element_ids, ELEMENT_IDS_REF).all()
        assert element_ids.flags.writeable
        # TODO check connectivity

    # check variables
    variable = case.get_variable("RTData")
    with open(variable.file_path, "rb") as fp:
        variable_data = variable.read_node_data(fp, part.part_id)
        assert variable_data.shape == VARIABLE_DATA_REF.shape
        assert variable_data.dtype == VARIABLE_DATA_REF.dtype
        assert np.allclose(variable_data, VARIABLE_DATA_REF)
        assert variable_data.flags.writeable


def test_read_sphere_case_mmap():
    # check casefile
    case = read_case(ENSIGHT_CASE_PATH)

    assert case.get_variables() == ["RTData"]
    assert case.get_node_variables() == ["RTData"]
    assert case.get_element_variables() == []

    assert not case.is_transient()
    assert case.get_time_values() is None

    # check geofile
    geofile = case.get_geometry_model()
    assert isinstance(geofile, EnsightGeometryFile)

    assert geofile.description_line1.startswith("Written by VTK EnSight Writer")
    assert geofile.description_line2.startswith("No Title was Specified")
    assert geofile.node_id_handling == IdHandling.GIVEN
    assert geofile.element_id_handling == IdHandling.GIVEN
    assert geofile.extents is None

    assert geofile.get_part_names() == ["VTK Part"]
    part = geofile.get_part_by_name("VTK Part")
    assert isinstance(part, GeometryPart)
    assert part.part_name == "VTK Part"
    assert geofile.parts[part.part_id] is part
    assert part.part_id == 1
    assert part.number_of_nodes == 50
    assert part.number_of_elements == 96

    with open(geofile.file_path, "rb") as fp_geo, mmap.mmap(fp_geo.fileno(), 0, access=mmap.ACCESS_READ) as mm_geo:
        nodes = part.read_nodes(mm_geo)
        assert nodes.shape == NODES_REF.shape
        assert nodes.dtype == NODES_REF.dtype
        assert np.allclose(nodes, NODES_REF)
        assert not nodes.flags.writeable

        node_ids = part.read_node_ids(mm_geo)
        assert node_ids.shape == NODE_IDS_REF.shape
        assert node_ids.dtype == NODE_IDS_REF.dtype
        assert np.equal(node_ids, NODE_IDS_REF).all()
        assert not nodes.flags.writeable

        assert len(part.element_blocks) == 1
        block = part.element_blocks[0]
        assert block.element_type == ElementType.TRIA3
        connectivity = block.read_connectivity(mm_geo)
        assert connectivity.shape == (96, 3)
        assert connectivity.dtype == np.int32
        assert not connectivity.flags.writeable

        element_ids = block.read_element_ids(mm_geo)
        assert element_ids.shape == ELEMENT_IDS_REF.shape
        assert element_ids.dtype == ELEMENT_IDS_REF.dtype
        assert np.equal(element_ids, ELEMENT_IDS_REF).all()
        assert not element_ids.flags.writeable

        # TODO check connectivity

    # check variables
    variable = case.get_variable("RTData")
    with open(variable.file_path, "rb") as fp_var, mmap.mmap(fp_var.fileno(), 0, access=mmap.ACCESS_READ) as mm_var:
        variable_data = variable.read_node_data(mm_var, part.part_id)
        assert variable_data.shape == VARIABLE_DATA_REF.shape
        assert variable_data.dtype == VARIABLE_DATA_REF.dtype
        assert np.allclose(variable_data, VARIABLE_DATA_REF)
        assert not variable_data.flags.writeable


def test_sphere_case_ensight2obj():
    with tempfile.TemporaryDirectory() as temp_dir:
        # TODO check output file
        assert 0 == ensight2obj(
            ensight_case_path=ENSIGHT_CASE_PATH,
            output_obj_path=op.join(temp_dir, "sphere.obj")
        )


def test_sphere_case_ensight2vtk():
    with tempfile.TemporaryDirectory() as temp_dir:
        # TODO check output file
        assert 0 == ensight2vtk(
            ensight_case_path=ENSIGHT_CASE_PATH,
            output_vtk_path_given=op.join(temp_dir, "sphere.vtk")
        )


NODES_REF = np.asarray([
    [0,0,5],
    [0,0,-5],
    [2.16942,0,4.50484],
    [3.90916,0,3.11745],
    [4.87464,0,1.1126],
    [4.87464,0,-1.1126],
    [3.90916,0,-3.11745],
    [2.16942,0,-4.50484],
    [1.53401,1.53401,4.50484],
    [2.76419,2.76419,3.11745],
    [3.44689,3.44689,1.1126],
    [3.44689,3.44689,-1.1126],
    [2.76419,2.76419,-3.11745],
    [1.53401,1.53401,-4.50484],
    [1.32839e-16,2.16942,4.50484],
    [2.39367e-16,3.90916,3.11745],
    [2.98486e-16,4.87464,1.1126],
    [2.98486e-16,4.87464,-1.1126],
    [2.39367e-16,3.90916,-3.11745],
    [1.32839e-16,2.16942,-4.50484],
    [-1.53401,1.53401,4.50484],
    [-2.76419,2.76419,3.11745],
    [-3.44689,3.44689,1.1126],
    [-3.44689,3.44689,-1.1126],
    [-2.76419,2.76419,-3.11745],
    [-1.53401,1.53401,-4.50484],
    [-2.16942,2.65677e-16,4.50484],
    [-3.90916,4.78734e-16,3.11745],
    [-4.87464,5.96971e-16,1.1126],
    [-4.87464,5.96971e-16,-1.1126],
    [-3.90916,4.78734e-16,-3.11745],
    [-2.16942,2.65677e-16,-4.50484],
    [-1.53401,-1.53401,4.50484],
    [-2.76419,-2.76419,3.11745],
    [-3.44689,-3.44689,1.1126],
    [-3.44689,-3.44689,-1.1126],
    [-2.76419,-2.76419,-3.11745],
    [-1.53401,-1.53401,-4.50484],
    [-3.98516e-16,-2.16942,4.50484],
    [-7.18101e-16,-3.90916,3.11745],
    [-8.95457e-16,-4.87464,1.1126],
    [-8.95457e-16,-4.87464,-1.1126],
    [-7.18101e-16,-3.90916,-3.11745],
    [-3.98516e-16,-2.16942,-4.50484],
    [1.53401,-1.53401,4.50484],
    [2.76419,-2.76419,3.11745],
    [3.44689,-3.44689,1.1126],
    [3.44689,-3.44689,-1.1126],
    [2.76419,-2.76419,-3.11745],
    [1.53401,-1.53401,-4.50484],
], dtype=np.float32)


NODE_IDS_REF = np.arange(50, dtype=np.int32)

VARIABLE_DATA_REF = np.asarray([
    220.841,
    220.841,
    223.809,
    233.508,
    217.599,
    217.599,
    233.508,
    223.809,
    212.899,
    239.063,
    234.323,
    234.323,
    239.063,
    212.899,
    223.057,
    235.175,
    208.477,
    208.477,
    235.175,
    223.057,
    211.23,
    244.044,
    234.086,
    234.086,
    244.044,
    211.23,
    220.563,
    224.501,
    227.629,
    227.629,
    224.501,
    220.563,
    230.677,
    218.349,
    210.127,
    210.127,
    218.349,
    230.677,
    221.315,
    222.833,
    236.751,
    236.751,
    222.833,
    221.315,
    232.346,
    213.368,
    210.363,
    210.363,
    213.368,
    232.346,
], dtype=np.float32)

ELEMENT_IDS_REF = np.arange(96, dtype=np.int32)
