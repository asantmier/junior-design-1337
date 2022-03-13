import numpy as np

class SSLedger:

    def __init__(self, ex):
        self.ex = ex

        # Create lists for sideset data
        self.num_ss = 0
        if ("num_side_sets" in ex.data.dimensions.keys()):
            self.num_ss = ex.data.dimensions["num_side_sets"].size
        self.ss_prop1 = [] # this is id for sideset
        self.ss_status = []
        self.ss_sizes = []
        self.ss_names = []
        self.num_dist_fact = []
        self.ss_dist_fact = []
        self.ss_elem = []
        self.ss_sides = []


        # Fill in lists with sideset data
        for i in range(self.num_ss):
            self.ss_prop1.append(ex.data["ss_prop1"][i]) 
            self.ss_status.append(ex.data["ss_status"][i])
            self.ss_sizes.append(ex.data.dimensions["num_side_ss" + str(i + 1)].size)
            if ("ss_names" in ex.data.variables):
                self.ss_names.append(self.ex.lineparse(ex.data["ss_names"][i]))
            else:
                self.ss_names.append("ss" + str(i))
            # if df do not exist, add size 0 arrays for them
            self.num_dist_fact.append(ex.get_sideset_params(self.ss_prop1[i])[1])
            self.ss_dist_fact.append(None)
            self.ss_elem.append(None) # this is place holder to be filled with real values later
            self.ss_sides.append(None) # this is place holder to be filled with real values later

    def add_sideset(self, elem_ids, side_ids, ss_id, ss_name, dist_fact):

        if (ss_id in self.ss_prop1):
            # already sideset with the same id
            raise Exception("Sideset with the same id already exists")
        
        if len(elem_ids) != len(side_ids):
            # do not have same number of elements and sides, throw error
            raise Exception("Number of element and number of sides do not match")

        if len(ss_name) > self.ex._MAX_NAME_LENGTH:
            raise Exception("Passed in name is too long")
        
        converted_elem_ids = elem_ids
        # converted_elem_ids = self.ex.lookup_id(elem_ids)

        # add sidesets to list
        self.ss_elem.append(converted_elem_ids)
        self.ss_sides.append(side_ids)
        self.ss_prop1.append(ss_id)
        self.ss_sizes.append(len(elem_ids))
        self.ss_status.append(1)
        self.ss_names.append(ss_name)
        self.num_dist_fact.append(len(dist_fact))
        self.ss_dist_fact.append(dist_fact)
        self.num_ss += 1 

    #TODO Replaced start of this with find_sideset_num, we should check that this still works
    def remove_sideset(self, ss_id):
        ndx = self.find_sideset_num(ss_id)
        
        # remove sideset from lists
        self.ss_prop1.pop(ndx)
        self.ss_status.pop(ndx)
        self.ss_names.pop(ndx)
        self.ss_elem.pop(ndx)
        self.ss_sizes.pop(ndx)
        self.ss_sides.pop(ndx)
        self.num_dist_fact.pop(ndx)
        self.ss_dist_fact.pop(ndx)
        self.num_ss -= 1

    def add_sides_to_sideset(self, elem_ids, side_ids, dist_facts, ss_id):
        ndx = self.find_sideset_num(ss_id)

        # if not loaded in yet, need to load in 
        if (self.ss_elem[ndx] is None):
            ss = self.ex.get_side_set(ss_id)
            elems = ss[0]
            sides = ss[1]
            self.ss_elem[ndx] = np.array(elems)
            self.ss_sides[ndx] = np.array(sides)
            self.ss_dist_fact[ndx] = np.array(self.ex.get_side_set_df(ss_id))

        
        self.ss_elem[ndx] = np.append(self.ss_elem[ndx], elem_ids)
        self.ss_sides[ndx] = np.append(self.ss_sides[ndx], side_ids)
        self.ss_dist_fact[ndx] = np.append(self.ss_dist_fact[ndx], dist_facts)
        self.ss_sizes[ndx] += len(elem_ids)
        self.num_dist_fact[ndx] += len(dist_facts)
    
    def remove_sides_from_sideset(self, elem_ids, side_ids, ss_id):
        pass





    # Creates 2 new sidesets from sides in old sideset based on x-coordinate values
    #TODO Would this work as a way to implement this function?
    #And what is the best way to get and check all nodes in the sideset?
    def split_sideset_x_coords(self, old_ss, comparison, x_value, all_nodes, ss_id1, ss_name1, ssid_2, ss_name2, delete):
        # Set comparison that will be used
        if comparison == '<':
          compare = lambda coord : coord < x_value
        elif comparison == '>':
          compare = lambda coord : coord > x_value
        elif comparison == '<=':
          compare = lambda coord : coord <= x_value
        elif comparison == '>=':
          compare = lambda coord : coord >= x_value
        elif comparison == '=':
          compare = lambda coord : coord == x_value
        elif comparison == '!=':
          compare = lambda coord : coord != x_value
        else:
          raise Exception("Comparison not valid. Valid comparison inputs: '<', '>', '<=', '>=', '=', '!='")

        # Get sideset that will be split
        ss_num = self.find_sideset_num(old_ss)
        
        # Create new sideset that will contain sides meeting user-specified criteria
        # dist_fact? create sideset before or after elems/sides found?
        #self.add_sideset([], [], ss_id1, ss_name1, [])

        # Create new sideset that will contain sides NOT meeting user-specified criteria
        # dist_fact? create sideset before or after elems/sides found?
        #self.add_sideset([], [], ss_id2, ss_name2, [])

        # Get all sides in old sideset
        # ???

        # Either add sides to new sideset if all nodes in a given side meet x-coord criteria
        #if all_nodes:
        #   For each side in old sideset
        #       flag = True
        #       For each node in side
        #           if not compare(current node x-coord):
        #               flag = False
        #               break
        #       if flag:
        #           self.add_side_to_ss(elem id of curr side, curr side id, ss_id1)
        #       else:
        #           self.add_side_to_ss(elem id of curr side, curr side id, ss_id2)

        # Or add sides to new sideset if at least one node in a given side meets x-coord criteria
        #else:
        #   For each side in old sideset
        #       flag = False
        #       For each node in side
        #           if compare(current node x-coord):
        #               flag = True
        #               break
        #       if flag:
        #           self.add_side_to_ss(elem id of curr side, curr side id, ss_id1)
        #       else:
        #           self.add_side_to_ss(elem id of curr side, curr side id, ss_id2)

        #Delete old sideset if desired by user
        # if delete:
        #    self.remove_sideset(old_ss)

    def write(self, data):

        if (self.num_ss == 0):
            # nothing to write so done
            return

        # write each dimension
        data.createDimension("num_side_sets", self.num_ss)
        for i in range(self.num_ss):
            data.createDimension("num_df_ss" + str(i + 1), self.num_dist_fact[i])
            data.createDimension("num_side_ss" + str(i+1), self.ss_sizes[i])

        # write each variable
        # copy over statuses
        data.createVariable("ss_status", "int32", dimensions=("num_side_sets"))
        data["ss_status"][:] = np.array(self.ss_status)
        # copy over ids
        data.createVariable("ss_prop1", "int32", dimensions=("num_side_sets"))
        data['ss_prop1'].setncattr('name', 'ID')
        data['ss_prop1'][:] = np.array(self.ss_prop1)

        # copy over names
        data.createVariable("ss_names", "|S1", dimensions=("num_side_sets", "len_name"))
        for i in range(len(self.ss_names)):
            data['ss_names'][i] = SSLedger.convert_string(self.ss_names[i] + str('\0'))

        for i in range(self.num_ss):
            # create elem, sides, and dist facts
            data.createVariable("elem_ss" + str(i+1), "int32", dimensions=("num_side_ss" + str(i+1)))
            data.createVariable("dist_fact_ss" + str(i+1), "int32", dimensions=("num_df_ss" + str(i+1)))
            data.createVariable("side_ss" + str(i+1), "float64", dimensions=("num_side_ss" + str(i+1)))
            
            # if None, just copy over old data, otherwise copy over new stuff
            if (self.ss_elem[i] is None):
                data["elem_ss" + str(i+1)][:] = self.ex.get_side_set(self.ss_prop1[i])[0][:]
            else:
                data["elem_ss" + str(i+1)][:] = self.ss_elem[i][:]

            if (self.ss_sides[i] is None):
                data["side_ss" + str(i+1)][:] = self.ex.get_side_set(self.ss_prop1[i])[1][:]
            else:
                data["side_ss" + str(i+1)][:] = self.ss_sides[i][:]
            
            if (self.ss_dist_fact[i] is None):
                data["dist_fact_ss" + str(i+1)][:] = self.ex.get_side_set_df(self.ss_prop1[i])[:]
            else:
                data["dist_fact_ss" + str(i+1)][:] = self.ss_dist_fact[i][:]

    # (Based on find_nodeset_num in ns_ledger)
    def find_sideset_num(self, ss_id):
        ndx = -1
        # search for sideset that corresponds with given ID
        for i in range(self.num_ss):
            if ss_id == self.ss_prop1[i]:
                # found id
                ndx = i
                break

        # raise IndexError if no nodeset is found
        if ndx == -1:
            raise IndexError("Cannot find sideset with ID " + str(ss_id))

        return ndx


    # method to convert python string to netcdf4 compatible character array
    @staticmethod
    def convert_string(s):
        arr = np.empty(33, '|S1')
        for i in range(len(s)):
            arr[i] = s[i]

        mask = np.empty(33, bool)
        for i in range(33):
            if i < len(s):
                mask[i] = False
            else:
                mask[i] = True

        out = np.ma.core.MaskedArray(arr, mask)
        return out  


