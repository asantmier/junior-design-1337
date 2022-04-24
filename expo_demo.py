from exodus import Exodus
from selector import ElementBlockSelector, PropertySelector
from output_subset import output_subset

if __name__ == "__main__":
    ex = Exodus("sample-files/biplane.exo", 'r')
    # Output the propeller to a new file
    # EB: 34, 35, 36, 37, 38
    eb_sels = [ElementBlockSelector(ex, 34), ElementBlockSelector(ex, 35), ElementBlockSelector(ex, 36),
               ElementBlockSelector(ex, 37), ElementBlockSelector(ex, 38)]
    output_subset(ex, "sample-files/propeller.exo", "Biplane Propeller", eb_sels, [], [], PropertySelector(ex))
