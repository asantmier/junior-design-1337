import warnings
import netCDF4 as nc
import numpy
from iterate import SampleFiles


class Exodus:
    _FORMAT_MAP = {'EX_NETCDF4': 'NETCDF4',
                   'EX_LARGE_MODEL': 'NETCDF3_64BIT_OFFSET',
                   'EX_NORMAL_MODEL': 'NETCDF3_CLASSIC',
                   'EX_64BIT_DATA': 'NETCDF3_64BIT_DATA'}
    # Default values
    _MAX_STR_LENGTH = 32
    _MAX_NAME_LENGTH = 32
    _MAX_LINE_LENGTH = 80
    _EXODUS_VERSION = 7.22

    # Should creating a new file (mode 'w') be a function on its own?
    def __init__(self, path, mode, shared=False, clobber=False, format='EX_NETCDF4', word_size=4):
        # clobber and format and word_size only apply to mode w
        if mode not in ['r', 'w', 'a']:
            raise ValueError("mode must be 'w', 'r', or 'a', got '{}'".format(mode))
        if format not in Exodus._FORMAT_MAP:
            raise ValueError("invalid file format: '{}'".format(format))
        if word_size not in [4, 8]:
            raise ValueError("word_size must be 4 or 8 bytes, {} is not supported".format(word_size))
        nc_format = Exodus._FORMAT_MAP[format]
        # Sets shared mdoe if the user asked for it. I have no idea what this does :)
        if shared:
            smode = mode + 's'
        else:
            smode = mode
        try:
            self.data = nc.Dataset(path, smode, clobber, format=nc_format)
        except FileNotFoundError:
            raise FileNotFoundError("file '{}' does not exist".format(path))
        except PermissionError:
            raise PermissionError("You do not have access to '{}'".format(path))
        except OSError:
            raise OSError("file '{}' exists, but clobber is set to False".format(path))

        if mode == 'w' or mode == 'a':
            # This is important according to ex_open.c
            self.data.set_fill_off()

        # We will read a bunch of data here to make sure it exists and warn the user if they might want to fix their
        # file. We don't save anything to memory so that if our data updates we don't have to update it in memory too.
        # This is the same practice used in the C library so its probably a good idea.

        # Initialize all the important parameters
        if mode == 'w':
            self.data.setncattr('title', 'Untitled database')
            self.data.createDimension('len_string', Exodus._MAX_STR_LENGTH + 1)
            self.data.createDimension('len_name', Exodus._MAX_NAME_LENGTH + 1)
            self.data.createDimension('len_line', Exodus._MAX_LINE_LENGTH + 1)
            self.data.setncattr('maximum_name_length', Exodus._MAX_NAME_LENGTH)
            self.data.setncattr('version', Exodus._EXODUS_VERSION)
            self.data.setncattr('api_version', Exodus._EXODUS_VERSION)
            self.data.setncattr('floating_point_word_size', word_size)
            file_size = 0
            if nc_format == 'NETCDF3_64BIT_OFFSET':
                file_size = 1
            self.data.setncattr('file_size', file_size)
            int64bit_status = 0
            if nc_format == 'NETCDF3_64BIT_DATA':
                int64bit_status = 1
            self.data.setncattr('int64_status', int64bit_status)

        # TODO Uncomment these later
        #  The C library doesn't seem to care if the file is in read or modify mode when it does this
        # Add this if it doesn't exist (value of 33)
        # if 'len_name' not in self.data.dimensions:
        #     warnings.warn("'len_name' dimension is missing!")

        # Add this if it doesn't exist (value of 32)
        # if 'maximum_name_length' not in self.data.ncattrs():
        #     warnings.warn("'maximum_name_length' attribute is missing!")

        # Check version compatibility
        ver = self.version
        if ver < 2.0:
            raise RuntimeError(
                "Unsupported file version {:.2f}! Only versions >2.0 are supported.".format(ver))

        # Read word size stored in file
        ws = self.word_size
        if ws == 4:
            self._float = numpy.float32
        elif ws == 8:
            self._float = numpy.float64
        else:
            raise ValueError("file contains a word size of {} which is not supported".format(ws))

        if self.int64_status == 0:
            self._int = numpy.int32
        else:
            self._int = numpy.int64

    def to_float(self, n):
        # Convert a number to the floating point type the database is using
        return self._float(n)

    def to_int(self, n):
        # Convert a number to the integer type the database is using
        return self._int(n)

    @property
    def float(self):
        # Returns floating point type of floating point numbers stored in the database
        # You may use whatever crazy types you want while coding, but convert them before storing them in the DB
        return self._float

    @property
    def int(self):
        # Returns integer type of integers stored in the database
        return self._int

    # TODO fix function that adds missing parts of the header
    # TODO function to find the longest name in the object

    # Everything in here that says it's the same as C is pretty much adapted 1-1 from the SEACAS Github and has been
    # double checked for speed. (see /libraries/exodus/src/ex_inquire.c)
    # Anything that says NOT IN C doesn't appear in the C version (to my knowledge) probably because the user does
    # not need to worry about that information and the user should not be able to modify it

    ########################################################################
    #                                                                      #
    #                        Data File Utilities                           #
    #                                                                      #
    ########################################################################

    # GLOBAL PARAMETERS

    # TODO perhaps in-place properties like these could have property setters as well

    # Same as C
    @property
    def title(self):
        try:
            return self.data.getncattr('title')
        except AttributeError:
            AttributeError("Database title could not be found")

    # Same as C
    @property
    def max_allowed_name_length(self):
        max_name_len = Exodus._MAX_NAME_LENGTH
        if 'len_name' in self.data.dimensions:
            # Subtract 1 because in C an extra null character is added for C reasons
            max_name_len = self.data.dimensions['len_name'].size - 1
        return max_name_len

    # Same as C
    @property
    def max_used_name_length(self):
        # 32 is the default size consistent with other databases
        max_used_name_len = 32
        if 'maximum_name_length' in self.data.ncattrs():
            # The length does not include the added null character from C
            max_used_name_len = self.data.getncattr('maximum_name_length')
        return max_used_name_len

    # Same as C
    @property
    def api_version(self):
        try:
            result = self.data.getncattr('api_version')
        except AttributeError:
            # Try the old way of spelling it
            try:
                result = self.data.getncattr('api version')
            except AttributeError:
                raise AttributeError("Exodus API version could not be found")
        return result

    # Same as C
    @property
    def version(self):
        try:
            return self.data.getncattr('version')
        except AttributeError:
            raise AttributeError("Exodus database version could not be found")

    # Same as C
    @property
    def num_qa(self):
        try:
            result = self.data.dimensions['num_qa_rec']
        except KeyError:
            result = 0
        return result

    # Same as C
    @property
    def num_info(self):
        try:
            result = self.data.dimensions['num_info']
        except KeyError:
            result = 0
        return result

    ########################################################################
    #                                                                      #
    #                        Model Description                             #
    #                                                                      #
    ########################################################################

    # Same as C
    @property
    def num_dim(self):
        try:
            return self.data.dimensions['num_dim'].size
        except KeyError:
            raise KeyError("database dimensionality could not be found")

    # Same as C
    @property
    def num_nodes(self):
        try:
            result = self.data.dimensions['num_nodes'].size
        except KeyError:
            # This and following functions don't actually error in C, they return 0. I assume there's a good reason.
            result = 0
        return result

    # Same as C
    @property
    def num_elem(self):
        try:
            result = self.data.dimensions['num_elem'].size
        except KeyError:
            result = 0
        return result

    # Same as C
    @property
    def num_elem_blk(self):
        try:
            result = self.data.dimensions['num_el_blk'].size
        except KeyError:
            result = 0
        return result

    # Same as C
    @property
    def num_node_sets(self):
        try:
            result = self.data.dimensions['num_node_sets'].size
        except KeyError:
            result = 0
        return result

    # TODO /libraries/exodus/src/ex_inquire.c line 382 and 387 contain functions we don't have about concatenated
    #  node sets. exodusII-new.pdf section 4.10 contains related information. I have no clue what this is but it's
    #  probably important. (Line 44 of that file looks related?)

    # Same as C
    @property
    def num_side_sets(self):
        try:
            result = self.data.dimensions['num_side_sets'].size
        except KeyError:
            result = 0
        return result

    # TODO Same deal as todo above. See lines 459, 561, and 566

    # Same as C
    @property
    def num_time_steps(self):
        try:
            return self.data.dimensions['time_step'].size
        except KeyError:
            raise KeyError("Number of database time steps could not be found")

    # TODO Similar to above, all of the _PROP functions (ctrl+f ex_get_num_props)

    # Same as C
    @property
    def num_elem_map(self):
        try:
            result = self.data.dimensions['num_elem_maps'].size
        except KeyError:
            result = 0
        return result

    # Same as C
    @property
    def num_node_map(self):
        try:
            result = self.data.dimensions['num_node_maps'].size
        except KeyError:
            result = 0
        return result

    # TODO Below line 695 stuff gets really weird. What on earth even is an edge set, face set, and elem set?

    # Same as C (i think)
    @property
    def num_node_var(self):
        try:
            return self.data.dimensions['num_nod_var'].size
        except KeyError:
            raise KeyError("Number of nodal variables could not be found")

    # Same as C (i think)
    @property
    def num_elem_block_var(self):
        try:
            return self.data.dimensions['num_elem_var'].size
        except KeyError:
            raise KeyError("Number of element block variables could not be found")

    # Same as C (i think)
    @property
    def num_node_set_var(self):
        try:
            return self.data.dimensions['num_nset_var'].size
        except KeyError:
            raise KeyError("Number of node set variables could not be found")

    # Same as C (i think)
    @property
    def num_side_set_var(self):
        try:
            return self.data.dimensions['num_sset_var'].size
        except KeyError:
            raise KeyError("Number of side set variables could not be found")

    # Same as C (i think)
    @property
    def num_global_var(self):
        try:
            return self.data.dimensions['num_glo_var'].size
        except KeyError:
            raise KeyError("Number of global variables could not be found")

    # Below are accessors for some data records that the C library doesn't seem to have
    # Not sure where file_size is useful. int64_status and word_size are probably only useful on initialization.
    # max_string/max_line_length are probably only useful on writing qa/info records. We can keep these for now but
    # delete them later once we determine they're actually useless

    # NOT IN C
    @property
    def file_size(self):
        # According to a comment in ex_utils.c @ line 1614
        # "Basically, the difference is whether the coordinates and nodal variables are stored in a blob (xyz components
        # together) or as a variable per component per nodal_variable."
        if 'file_size' in self.data.ncattrs():
            return self.data.getncattr('file_size')
        else:
            return 1 if self.data.data_model == 'NETCDF3_64BIT_OFFSET' else 0
            # No warning is raised because older files just don't have this

    # NOT IN C (only used in ex_open.c)
    @property
    def int64_status(self):
        # Determines whether or not the file uses int64s
        if 'int64_status' in self.data.ncattrs():
            return self.data.getncattr('int64_status')
        else:
            return 1 if self.data.data_model == 'NETCDF3_64BIT_DATA' else 0
            # No warning is raised because older files just don't have this

    # NOT IN C (only used in ex_open.c)
    @property
    def word_size(self):
        try:
            result = self.data.getncattr('floating_point_word_size')
        except AttributeError:
            try:
                result = self.data.getncattr('floating point word size')
            except AttributeError:
                # This should NEVER happen, but here to be safe
                raise AttributeError("Exodus database floating point word size could not be found")
        return result

    # NOT IN C
    @property
    def max_string_length(self):
        # See ex_put_qa.c @ line 119. This record is created and used when adding QA records
        max_str_len = Exodus._MAX_STR_LENGTH
        if 'len_string' in self.data.dimensions:
            # Subtract 1 because in C an extra character is added for C reasons
            max_str_len = self.data.dimensions['len_string'].size - 1
        return max_str_len

    # NOT IN C
    @property
    def max_line_length(self):
        # See ex_put_info.c @ line 121. This record is created and used when adding info records
        max_line_len = Exodus._MAX_LINE_LENGTH
        if 'len_line' in self.data.dimensions:
            # Subtract 1 because in C an extra character is added for C reasons
            max_line_len = self.data.dimensions['len_line'].size - 1
        return max_line_len

    @property
    def qa_records(self):
        lst = []
        for line in self.data.variables['qa_records'][0]:
            lst.append(Exodus.lineparse(line))
        return lst

    @property
    def info_records(self):
        lst = []
        for line in self.data.variables['info_records']:
            lst.append(Exodus.lineparse(line))
        return lst

    @property
    def time_values(self):
        """Returns a list of (float) time values for each time step"""
        values = []
        for step in self.time_steps:
            values.append(self.timeAtStep(step))
        return values

    @property
    def time_steps(self):
        """Returns list of the time steps, 0-indexed"""
        return [*range(self.num_time_steps)]

    def timeAtStep(self, step):
        """Given an integer time step, return the corresponding float time value"""
        return float(self.data['time_whole'][step].data)

    def stepAtTime(self, time):
        """Given a float time value, return the corresponding time step"""
        for index, value in enumerate(self.time_values):
            if value == time:
                return index
        return None

    def get_dimension(self, name):
        if name in self.data.dimensions:
            return self.data.dimensions[name].size
        else:
            raise RuntimeError("dimensions '{}' cannot be found!".format(name))

    def get_parameter(self, name):
        if name in self.data.ncattrs():
            return self.data.getncattr(name)
        else:
            raise RuntimeError("parameter '{}' cannot be found!".format(name))

    def close(self):
        self.data.close()

    def print_dimensions(self):
        for dim in self.data.dimensions.values():
            print(dim)

    def print_dimension_names(self):
        for dim in self.data.dimensions:
            print(dim)

    def print_variables(self):
        for v in self.data.variables.values():
            print(v, "\n")

    def print_variable_names(self):
        for v in self.data.variables:
            print(v)

    def get_sideset(self, id):
        ndx = id - 1

        if ("ss_prop1" in self.data.variables):
            ndx = numpy.where(self.data.variables["ss_prop1"][:] == id)[0][0]
            ndx += 1

        elem_key = 'elem_ss' + str(ndx)
        side_key = 'side_ss' + str(ndx)
        sideset_i = {}

        if elem_key in self.data.variables and side_key in self.data.variables:
            if ("elem_num_map" in self.data.variables):
                sideset_i['elements'] = self.data["elem_num_map"][self.data[elem_key][:]]
            else:
                sideset_i['elements'] = self.data[elem_key][:]
            sideset_i['sides'] = self.data[side_key][:]
        else:
            raise RuntimeError("sideset '{}' cannot be found!".format(id))

        return sideset_i

    def get_nodeset(self, id):
        ndx = id - 1
        if ("ns_prop1" in self.data.variables):
            ndx = numpy.where(self.data.variables["ns_prop1"][:] == id)[0][0]
            ndx += 1

        key = "node_ns" + str(ndx)
        if ("node_num_map" in self.data.variables):
            print(self.data[key][:])
            return self.data["node_num_map"][self.data[key][:]]
        return self.data[key][:]


    def set_nodeset(self, node_set_id, node_ids):
        ndx = node_set_id - 1
        if ("ns_prop1" in self.data.variables):
            ndx = numpy.where(self.data.variables["ns_prop1"][:] == node_set_id)[0][0]
            ndx += 1
        
        key = "node_ns" + str(ndx)
        nodeset = self.data[key]

        if ("node_num_map" in self.data.variables):
            indices = numpy.zeros(len(node_ids))
            i = 0
            for id in node_ids:
                ndx = numpy.where(self.data["node_num_map"][:] == id)[0][0]
                indices[i] = ndx
                i += 1
            nodeset[:] = indices
            return
        nodeset[:] = node_ids

    # def add_nodeset(self, node_ids):
    #     # self.data.createDimension("num_nod_ns4", len(node_ids))
    #     # self.data.createVariable("node_ns4", numpy.dtype('i4'), ("num_nod_ns4"))

    #     self.data.dimensions["num_node_sets"].size += 1
    #     # if ("node_num_map" not in self.data.variables):
    #     #     self.data["node_ns4"][:] = node_ids
    #     #     return

    #     # i = 0
    #     # for id in node_ids:
    #     #     ndx = numpy.where(self.data["node_num_map"][:] == id)[0][0]
    #     #     self.data["node_ns4"][i] = ndx
    #     #     i += 1

    def get_nodes_in_elblock(self, id):
        if ("node_num_map" in self.data.variables):
            raise Exception("Using node num map")
        nodeids = self.data["connect" + str(id)]
        # flatten it into 1d
        nodeids = nodeids[:].flatten()   
        return nodeids


    def edit_coords(self, node_ids, dim, displace):
        if ("node_num_map" in self.data.variables):
            raise Exception("Using node num map")
        node_ndxs = node_ids - 1
        dimnum = 0
        if (dim == 'y'):
            dimnum = 1
        elif (dim == 'z'):
            dimnum = 2
        self.data["coord"][dimnum, node_ndxs] += displace

    # prints legacy character array as string
    @staticmethod
    def print(line):
        print(Exodus.lineparse(line))

    @staticmethod
    def lineparse(line):
        s = ""
        for c in line:
            if str(c) != '--':
                s += str(c)[2]

        return s


if __name__ == "__main__":
    ex = Exodus("sample-files/cube_1ts_mod.e", 'r')
    print(ex.data)
    # with warnings.catch_warnings():
    #     warnings.simplefilter('ignore')
    #     for file in SampleFiles():
    #         ex = Exodus(file, 'r')
    #         try:
    #             print(ex.data)
    #         except KeyError:
    #             print("no QA record found")
    #     ex.close()
