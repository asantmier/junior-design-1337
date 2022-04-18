import pytest
import numpy as np
from exodus import Exodus
from selector import ElementBlockSelector, NodeSetSelector, SideSetSelector, PropertySelector
from constants import *
from output_subset import output_subset

# Disables all warnings in this module
pytestmark = pytest.mark.filterwarnings('ignore')


# pytest-dependency might be useful in here to require the read tests to pass...

# It's probably worth doing a test that only copies part of each thing in a file
# A test that copies everything, but not node sets
# Also you could just delete the id maps and see if everything works out still
# The most breakable part involves the node list
def test_partial_side_set(tmpdir):
    pass


# Test output_subset, selecting the entire model
def test_whole_subset(tmpdir):
    input_file = Exodus("sample-files/cube_1ts_mod.e", 'r')
    p = str(tmpdir) + '\\output_test.ex2'
    t = "test whole subset"
    eb_sels = []
    for obj_id in input_file.get_elem_block_id_map():
        sel = ElementBlockSelector(input_file, obj_id)
        eb_sels.append(sel)
    ss_sels = []
    for obj_id in input_file.get_side_set_id_map():
        sel = SideSetSelector(input_file, obj_id)
        ss_sels.append(sel)
    ns_sels = []
    for obj_id in input_file.get_node_set_id_map():
        sel = NodeSetSelector(input_file, obj_id)
        ns_sels.append(sel)
    prop_sel = PropertySelector(input_file)
    nodal_var = list(range(1, input_file.num_node_var + 1))
    global_var = list(range(1, input_file.num_global_var + 1))
    steps = list(range(1, input_file.num_time_steps + 1))

    output_subset(input_file, p, t, eb_sels, ss_sels, ns_sels, prop_sel, nodal_var, global_var, steps)

    output_file = Exodus(p, 'r')

    assert_required_features(input_file, output_file, t, steps)

    assert output_file.num_global_var == input_file.num_global_var
    assert output_file.num_node_var == input_file.num_node_var
    assert output_file.num_time_steps == input_file.num_time_steps
    assert output_file.num_elem_blk == input_file.num_elem_blk
    assert output_file.num_node_sets == input_file.num_node_sets
    assert output_file.num_side_sets == input_file.num_side_sets
    assert output_file.num_elem == input_file.num_elem
    assert output_file.num_nodes == input_file.num_nodes

    # Before anything, we need to make sure ID maps carried over
    assert np.array_equal(output_file.get_node_id_map(), input_file.get_node_id_map())
    assert np.array_equal(output_file.get_elem_id_map(), input_file.get_elem_id_map())
    assert np.array_equal(output_file.get_elem_block_id_map(), input_file.get_elem_block_id_map())
    assert np.array_equal(output_file.get_node_set_id_map(), input_file.get_node_set_id_map())
    assert np.array_equal(output_file.get_side_set_id_map(), input_file.get_side_set_id_map())

    # Element order map
    assert np.array_equal(output_file.get_elem_order_map(), input_file.get_elem_order_map())

    # Nodal and global variables
    if output_file.has_var_names(NODAL_VAR):
        assert np.array_equal(output_file.get_nodal_var_names(), input_file.get_nodal_var_names())
    if output_file.has_var_names(GLOBAL_VAR):
        assert np.array_equal(output_file.get_global_var_names(), input_file.get_global_var_names())
    for i in range(input_file.num_node_var):
        assert np.array_equal(output_file.get_nodal_var_across_times(1, output_file.num_time_steps, i + 1),
                              input_file.get_nodal_var_across_times(1, input_file.num_time_steps, i + 1))
    for i in range(input_file.num_global_var):
        assert np.array_equal(output_file.get_global_var_across_times(1, output_file.num_time_steps, i + 1),
                              input_file.get_global_var_across_times(1, input_file.num_time_steps, i + 1))

    # Coordinates
    assert np.array_equal(output_file.get_coord_names(), input_file.get_coord_names())
    assert np.array_equal(output_file.get_coords(), input_file.get_coords())

    # Node sets
    # Names
    assert np.array_equal(output_file.get_node_set_names(), input_file.get_node_set_names())
    # Variables
    assert output_file.num_node_set_var == input_file.num_node_set_var
    assert np.array_equal(output_file.get_node_set_truth_table(), input_file.get_node_set_truth_table())
    if input_file.has_var_names(NODESET_VAR):
        assert np.array_equal(output_file.get_node_set_var_names(), input_file.get_node_set_var_names())
    # Properties
    assert output_file.num_node_set_prop == input_file.num_node_set_prop
    assert np.array_equal(output_file.get_node_set_property_names(), input_file.get_node_set_property_names())
    for n in input_file.get_node_set_property_names():
        assert np.array_equal(output_file.get_node_set_property_array(n), input_file.get_node_set_property_array(n))
    # Per node set comparison
    for i in input_file.get_node_set_id_map():
        out_nod, out_df = output_file.get_node_set_params(i)
        in_nod, in_df = input_file.get_node_set_params(i)
        # Nodes
        assert out_nod == in_nod
        assert np.array_equal(output_file.get_node_set(i), input_file.get_node_set(i))
        # Dist fact
        assert out_df == in_df
        assert np.array_equal(output_file.get_node_set_df(i), input_file.get_node_set_df(i))
        # Variables
        for j in range(input_file.num_node_set_var):
            assert np.array_equal(output_file.get_node_set_var_across_times(i, 1, output_file.num_time_steps, j + 1),
                                  input_file.get_node_set_var_across_times(i, 1, input_file.num_time_steps, j + 1))

    # Element blocks
    # Names
    assert np.array_equal(output_file.get_elem_block_names(), input_file.get_elem_block_names())
    # Variables
    assert output_file.num_elem_block_var == input_file.num_elem_block_var
    assert np.array_equal(output_file.get_elem_block_truth_table(), input_file.get_elem_block_truth_table())
    if input_file.has_var_names(ELEMENTAL_VAR):
        assert np.array_equal(output_file.get_elem_var_names(), input_file.get_elem_var_names())
    # Properties
    assert output_file.num_elem_block_prop == input_file.num_elem_block_prop
    assert np.array_equal(output_file.get_elem_block_property_names(), input_file.get_elem_block_property_names())
    for n in input_file.get_elem_block_property_names():
        assert np.array_equal(output_file.get_elem_block_property_array(n),
                              input_file.get_elem_block_property_array(n))
    # Per element block comparison
    for i in input_file.get_elem_block_id_map():
        out_el, out_nel, out_top, out_att = output_file.get_elem_block_params(i)
        in_el, in_nel, in_top, in_att = input_file.get_elem_block_params(i)
        # Elements
        assert out_nel == in_nel
        assert out_top == in_top
        assert out_el == out_el
        assert np.array_equal(output_file.get_elem_block_connectivity(i), input_file.get_elem_block_connectivity(i))
        # Attributes
        assert out_att == in_att
        assert output_file.get_num_elem_attrib(i) == input_file.get_num_elem_attrib(i)
        assert np.array_equal(output_file.get_elem_attrib_names(i), input_file.get_elem_attrib_names(i))
        assert np.array_equal(output_file.get_elem_attrib(i), input_file.get_elem_attrib(i))
        # Variables
        for j in range(input_file.num_elem_block_var):
            assert np.array_equal(
                output_file.get_elem_block_var_across_times(i, 1, output_file.num_time_steps, j + 1),
                input_file.get_elem_block_var_across_times(i, 1, input_file.num_time_steps, j + 1))

    # Side sets
    # Names
    assert np.array_equal(output_file.get_side_set_names(), input_file.get_side_set_names())
    # Variables
    assert output_file.num_side_set_var == input_file.num_side_set_var
    assert np.array_equal(output_file.get_side_set_truth_table(), input_file.get_side_set_truth_table())
    if input_file.has_var_names(SIDESET_VAR):
        assert np.array_equal(output_file.get_side_set_var_names(), input_file.get_side_set_var_names())
    # Properties
    assert output_file.num_side_set_prop == input_file.num_side_set_prop
    assert np.array_equal(output_file.get_side_set_property_names(), input_file.get_side_set_property_names())
    for n in input_file.get_side_set_property_names():
        assert np.array_equal(output_file.get_side_set_property_array(n), input_file.get_side_set_property_array(n))
    # Per side set comparison
    for i in input_file.get_side_set_id_map():
        out_num_el, out_num_df = output_file.get_side_set_params(i)
        in_num_el, in_num_df = input_file.get_side_set_params(i)
        out_el, out_side = output_file.get_side_set(i)
        in_el, in_side = input_file.get_side_set(i)
        # Elements and their sides
        assert out_num_el == in_num_el
        assert np.array_equal(out_el, in_el)
        assert np.array_equal(out_side, in_side)
        # Dist fact
        assert out_num_df == in_num_df
        assert np.array_equal(output_file.get_side_set_df(i), input_file.get_side_set_df(i))
        # Variables
        for j in range(input_file.num_side_set_var):
            assert np.array_equal(
                output_file.get_side_set_var_across_times(i, 1, output_file.num_time_steps, j + 1),
                input_file.get_side_set_var_across_times(i, 1, input_file.num_time_steps, j + 1))

    output_file.close()
    input_file.close()


# Tests output_subset with all empty arguments
def test_empty_subset(tmpdir):
    input_file = Exodus("sample-files/cube_1ts_mod.e", 'r')
    p = str(tmpdir) + '\\output_test.ex2'
    t = ""
    eb_sels = []
    ss_sels = []
    ns_sels = []
    prop_sel = PropertySelector(input_file, None, None, None)
    nodal_var = []
    global_var = []
    steps = []

    output_subset(input_file, p, t, eb_sels, ss_sels, ns_sels, prop_sel, nodal_var, global_var, steps)

    output_file = Exodus(p, 'r')

    assert_required_features(input_file, output_file, t, steps)

    assert output_file.num_global_var == 0
    assert output_file.num_node_var == 0
    assert output_file.num_time_steps == 0
    assert output_file.num_elem_blk == 0
    assert output_file.num_node_sets == 0
    assert output_file.num_side_sets == 0
    assert output_file.num_elem == 0
    assert output_file.num_nodes == 0
    # If those dimensions were right, there's no need to check the variables because their dimensions would be 0.
    # Not to mention this is already an invalid Exodus file...

    output_file.close()
    input_file.close()


# Checks existence and validity of all necessary Exodus II features in a subset file
def assert_required_features(input_file, output_file, t, steps):
    # Required parameters list taken from Exodus II documentation (SAND92-2137)
    assert ATT_TITLE in output_file.data.ncattrs()
    assert DIM_LINE_LENGTH in output_file.data.dimensions
    assert DIM_NUM_NODES in output_file.data.dimensions
    assert DIM_NUM_DIM in output_file.data.dimensions
    assert DIM_NUM_ELEM in output_file.data.dimensions
    assert ATT_API_VER in output_file.data.ncattrs()
    assert ATT_VERSION in output_file.data.ncattrs()
    assert ATT_WORD_SIZE in output_file.data.ncattrs()
    assert DIM_STRING_LENGTH in output_file.data.dimensions
    assert DIM_LINE_LENGTH in output_file.data.dimensions
    # Below parameters are not explicitly defined as necessary, but are strongly suggested to be
    assert DIM_NAME_LENGTH in output_file.data.dimensions
    assert DIM_NUM_TIME_STEP in output_file.data.dimensions
    assert VAR_TIME_WHOLE in output_file.data.variables

    # Check that values were copied over correctly
    assert output_file.title == t
    assert output_file.max_used_name_length == input_file.max_used_name_length
    assert output_file.api_version == input_file.api_version
    assert output_file.version == input_file.version
    assert output_file.large_model == input_file.large_model
    assert output_file.int64_status == input_file.int64_status
    assert output_file.word_size == input_file.word_size
    assert output_file.max_allowed_name_length == input_file.max_allowed_name_length
    assert output_file.max_string_length == input_file.max_string_length
    assert output_file.max_line_length == input_file.max_line_length
    assert output_file.num_dim == input_file.num_dim
    assert output_file.data.dimensions[DIM_FOUR].size == 4

    assert output_file.num_qa == input_file.num_qa + 1
    if input_file.num_qa > 0:
        assert np.array_equal(output_file.data.variables[VAR_QA][:input_file.num_qa], input_file.data.variables[VAR_QA])

    assert output_file.num_info == input_file.num_info
    if input_file.num_info > 0:
        assert np.array_equal(output_file.data.variables[VAR_INFO], input_file.data.variables[VAR_INFO])

    assert output_file.num_time_steps == len(steps)
    # Output subset sorts this so we must too
    sorted_steps = steps
    sorted_steps.sort()
    sorted_steps_idx = [x - 1 for x in sorted_steps]
    if input_file.num_time_steps > 0:
        assert np.array_equal(output_file.data.variables[VAR_TIME_WHOLE][:],
                              input_file.data.variables[VAR_TIME_WHOLE][:][sorted_steps_idx])

    assert output_file.int == input_file.int
    assert output_file.float == output_file.float
