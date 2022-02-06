import pytest
import numpy
import netCDF4
import exodus as exo

# Disables all warnings in this module
pytestmark = pytest.mark.filterwarnings('ignore')

def test_open():
    # Test that we can open a file without any errors
    exofile = exo.Exodus('sample-files/disk_out_ref.ex2', 'r')
    assert exofile.data
    exofile.close()


#TODO: Test fails (AttributeError: 'LocalPath' object has no attribute 'split')
def test_create(tmpdir):
    # Test that we can create a file without any errors
    exofile = exo.Exodus(tmpdir + '/test.ex2', 'w')
    assert exofile.data
    exofile.close()


#TODO: Test fails (ValueError: file must be an exodus file with extension .e or .ex2)
def test_exodus_init_exceptions(tmp_path, tmpdir):
    # Test that the Exodus.__init__() errors all work
    with pytest.raises(FileNotFoundError):
        exofile = exo.Exodus('some fake directory/notafile.xxx', 'r')
    with pytest.raises(ValueError):
        exofile = exo.Exodus('sample-files/disk_out_ref.ex2', 'z')
    with pytest.raises(OSError):
        exofile = exo.Exodus(tmp_path, 'w', False)
    with pytest.raises(ValueError):
        exofile = exo.Exodus(tmpdir + '/test.ex2', 'w', True, "NOTAFORMAT")
    with pytest.raises(PermissionError):
        exofile = exo.Exodus(tmp_path, 'w', True)
    with pytest.raises(ValueError):
        exofile = exo.Exodus(tmpdir + '/test2.ex2', 'w', True, "NETCDF4", 7)


#TODO: Test fails (AttributeError: 'LocalPath' object has no attribute 'split')
def test_float(tmpdir):
    exofile = exo.Exodus(tmpdir + '/test.ex2', 'w', word_size=4)
    assert type(exofile.to_float(1.2)) == numpy.single
    exofile = exo.Exodus(tmpdir + '/test2.ex2', 'w', word_size=8)
    assert type(exofile.to_float(1.2)) == numpy.double
    exofile.close()


#TODO: Test fails (AttributeError: Exodus' object has no attribute 'parameters')
def test_parameters():
    exofile = exo.Exodus('sample-files/disk_out_ref.ex2', 'r')
    assert exofile.parameters
    assert exofile.title
    assert exofile.version
    assert exofile.api_version
    assert exofile.word_size
    exofile.close()


def test_get_node_set():
    # Testing that get_node_set returns accurate info based on info from Coreform Cubit
    # 'can.ex2' has 1 nodeset (ID 1) with 444 nodes and 1 nodeset (ID 100) with 164 nodes
    exofile = exo.Exodus('sample-files/can.ex2', 'r')
    assert len(exofile.get_node_set(1)) == 444
    assert len(exofile.get_node_set(100)) == 164
    exofile.close
    # 'cube_1ts_mod.e' has 6 nodesets (ID 1-6) with 81 nodes and 1 nodeset (ID 7) with 729 nodes
    exofile = exo.Exodus('sample-files/cube_1ts_mod.e', 'r')
    i = 1
    while i <= 6:
        nodeset = exofile.get_node_set(i)
        assert len(nodeset) == 81
        i += 1
    assert len(exofile.get_node_set(7)) == 729
    exofile.close()
    # Nodeset 1 in 'disk_out_ref.ex2' has 1 node with ID 7210
    exofile = exo.Exodus('sample-files/disk_out_ref.ex2', 'r')
    nodeset = exofile.get_node_set(1)
    assert nodeset[0] == 7210
    exofile.close()


def test_get_side_set():
    # Testing that get_side_set returns accurate info based on info from Coreform Cubit
    # 'can.ex2' has 1 sideset (ID 4) with 120 elements and 120 sides
    exofile = exo.Exodus('sample-files/can.ex2', 'r')
    sideset = exofile.get_side_set(4)
    assert len(sideset[0]) == 120
    assert len(sideset[1]) == 120
    exofile.close
    # Elem+side counts found in Cubit using "list sideset #" command where # is ID
    # 'disk_out_ref.ex2' has 7 sidesets (ID 1-7) with varying amounts of elements/sides
    exofile = exo.Exodus('sample-files/disk_out_ref.ex2', 'r')
    # ID 1: 418 elements (209 * 2 surfaces), 418 side count
    sideset = exofile.get_side_set(1)
    assert len(sideset[0]) == 418
    assert len(sideset[1]) == 418
    # ID 2: 180 elements (90 * 2 surfaces), 180 side count
    sideset = exofile.get_side_set(2)
    assert len(sideset[0]) == 180
    assert len(sideset[1]) == 180
    # ID 3: 828 elements (414 * 2 surfaces), 828 side count
    sideset = exofile.get_side_set(3)
    assert len(sideset[0]) == 828
    assert len(sideset[1]) == 828
    # ID 4: 238 elements (119 * 2 surfaces), 238 side count
    sideset = exofile.get_side_set(4)
    assert len(sideset[0]) == 238
    assert len(sideset[1]) == 238
    # ID 5: 108 elements (54 * 2 surfaces), 108 side count
    sideset = exofile.get_side_set(5)
    assert len(sideset[0]) == 108
    assert len(sideset[1]) == 108
    # ID 6: 216 elements (108 * 2 surfaces), 216 side count
    sideset = exofile.get_side_set(6)
    assert len(sideset[0]) == 216
    assert len(sideset[1]) == 216
    # ID 7: 482 elements (482 * 1 surface), 482 side count
    # BUT along one face in Cubit so 2 sides/elements counted as 1
    # Technically 964 elements and 964 sides in Exodus file
    sideset = exofile.get_side_set(7)
    assert len(sideset[0]) == 964
    assert len(sideset[1]) == 964
    exofile.close()


def test_get_coords():
    # Testing that get_coords returns accurate info based on info from Coreform Cubit
    # 'cube_1ts_mod.e' has 729 coords (ID 1-729) and 3 dimensions (xyz)
    exofile = exo.Exodus('sample-files/cube_1ts_mod.e', 'r')
    coords = exofile.get_coords()
    # 3 coordinates per node
    assert len(coords == (729*3))
    # x, y, and z coordinates for each node
    assert len(coords[0]) == len(coords[1]) == len(coords[2])
    # Test coords read correctly for some nodes
    # (Array index from 0, IDs start at 1)
    # Node ID 133 coords: (.125, -.25, -.5)
    assert coords[0][132] == .125
    assert coords[1][132] == -.25
    assert coords[2][132] == -.5
    # Node ID 337 coords: (-.375, .5, -.375)
    assert coords[0][336] == -.375
    assert coords[1][336] == .5
    assert coords[2][336] == -.375
    exofile.close()

def test_get_coord_x():
    # Testing that get_coord_x returns accurate info based on info from Coreform Cubit
    # 'cube_1ts_mod.e' has 729 coords (ID 1-729) and 3 dimensions (xyz)
    exofile = exo.Exodus('sample-files/cube_1ts_mod.e', 'r')
    xcoords = exofile.get_coord_x()
    # 729 nodes
    assert len(xcoords == 729)
    # Test x coord is read correctly for some nodes
    # (Array index from 0, IDs start at 1)
    # Node ID 11 x coord: .375
    assert xcoords[10] == .375
    # Node ID 194 x coord: -.125
    assert xcoords[193] == -.125
    exofile.close()

def test_get_coord_y():
    # Testing that get_coord_y returns accurate info based on info from Coreform Cubit
    # 'cube_1ts_mod.e' has 729 coords (ID 1-729) and 3 dimensions (xyz)
    exofile = exo.Exodus('sample-files/cube_1ts_mod.e', 'r')
    ycoords = exofile.get_coord_y()
    # 729 nodes
    assert len(ycoords == 729)
    # Test y coord is read correctly for some nodes
    # (Array index from 0, IDs start at 1)
    # Node ID 22 y coord: 0
    assert ycoords[21] == 0
    # Node ID 202 y coord: -.5
    assert ycoords[201] == -.5
    exofile.close()

def test_get_coord_z():
    # Testing that get_coord_z returns accurate info based on info from Coreform Cubit
    # 'cube_1ts_mod.e' has 729 coords (ID 1-729) and 3 dimensions (xyz)
    exofile = exo.Exodus('sample-files/cube_1ts_mod.e', 'r')
    zcoords = exofile.get_coord_z()
    # 729 nodes
    assert len(zcoords == 729)
    # Test z coord is read correctly for some nodes
    # (Array index from 0, IDs start at 1)
    # Node ID 365 z coord: -.375
    assert zcoords[364] == -.375
    # Node ID 563 z coord: .25
    assert zcoords[562] == .25
    exofile.close()


# Below tests are based on what can be read according to current C Exodus API.
# The contents, names, and number of tests are subject to change as work on the library progresses
# and we figure out how closely the functions in this library match the C one.

# MODEL DESCRIPTION READ TESTS
# def test_get_coords():
# def test_get_coord_names():
# def test_get_node_num_map():
# def test_get_elem_num_map():
# def test_get_elem_order_map():
# def test_get_elem_blk_params():
# def test_get_elem_blk_IDs():
# def test_get_elem_blk_connect():
# def test_get_nodeset_params():
# def test_get_nodeset_dist_fact():
# def test_get_nodeset_IDs():
# def test_get_concat_nodesets():
# def test_get_sideset_params():
# def test_get_sideset():
# def test_get_sideset_dist_fact():
# def test_get_sideset_IDs():
# def test_get_sideset_node_list():
# def test_get_concat_sidesets():
# def test_get_prop_names():
# def test_get_prop():
# def test_get_prop_array():

# RESULTS DATA READ TESTS
# def test_get_variable_params():
# def test_get_variable_names():
# def test_get_time():
# def test_get_all_times():
# def test_get_elem_var_table():
# def test_get_elem_var():
# def test_get_elem_var_time():
# def test_get_glob_vars():
# def test_get_glob_var_time():
# def test_get_nodal_var():
# def test_get_nodal_var_time():