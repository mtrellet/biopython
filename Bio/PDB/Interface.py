# Copyright (C) 2011, Mikael Trellet (mikael.trellet@gmail.com)
# This code is part of the Biopython distribution and governed by its
# license.  Please see the LICENSE file that should have been included
# as part of this package.

"""Interface class, used in Structure objects."""

from Bio.PDB.Entity import Entity
from Bio.Data import IUPACData
from Bio.SCOP.Raf import to_one_letter_code
from Bio.PDB.PDBParser import PDBParser
from Bio.PDB.NACCESS import NACCESS
from Bio.PDB.NACCESS import NACCESS_atomic


class Interface(Entity):
    """
    The Interface object isn't automatically initialize during a PDB parsing,
    but can be guessed from an existing parsed structure in order to analyse
    the interface between 2 or more chains in a complex.
    """

    def __init__(self, id, model):
        self.level="I"
        self.id=id
        self.model=model
        self.neighbors = {}
        self.uniq_pairs = []

        Entity.__init__(self, id)

    # Override Entity add method
    # Interface doesnt follow strictly
    # other Entity rules.
    #
    # Its childs are residues
    # but it may be useful
    # to list them by chain.
    
    def add(self, entity):
        "Add a child to the Entity."

        entity_id=entity.get_id()
        if not self.has_id(entity_id):

            self.child_list.append(entity)
            if entity.parent.id not in self.child_dict:
                self.child_dict[entity.parent.id] = []
            self.child_dict[entity.parent.id].append(entity)

    def get_chains(self):
        "Get the different chains involved in the Interface object"
        for chain in self.child_dict.keys():
            yield chain

    def set_neighbors(self):
        "Creates residues list of neighbors"
        ## Initializes neighbors dictionnary with interface chains
        for c in self.get_chains():
            self.neighbors[c]={}
            
        for resA, resB in self.uniq_pairs:
        ## Checking for 1st residue (if his chain exist, then if 
        ## it is referenced and finally if his partner is already present)
            if resA not in self.neighbors[resA.parent.id]:
                self.neighbors[resA.parent.id][resA]=[]
                self.neighbors[resA.parent.id][resA].append(resB)
            elif resB not in self.neighbors[resA.parent.id][resA]:
                self.neighbors[resA.parent.id][resA].append(resB)
        ## Checking for 2nd residue
            if resB not in self.neighbors[resB.parent.id]:
                self.neighbors[resB.parent.id][resB]=[]
                self.neighbors[resB.parent.id][resB].append(resB)
            elif resA not in self.neighbors[resB.parent.id][resB]:
                self.neighbors[resB.parent.id][resB].append(resA)
        neighbors=self.neighbors
        return neighbors

    def calculate_percentage(self):
        "Gets the percentage of polar/apolar/charged residues at the interface"
        
        polar=0
        apolar=0
        charged=0
        polar_list=getattr(IUPACData, "protein_polarity")
        charged_list=getattr(IUPACData, "protein_pka_side_chain")
        for r in self:
            res=to_one_letter_code[r.resname]
            if res in polar_list['polar']:
                if charged_list[res]:
                    charged=charged+1
                else:
                    polar=polar+1
            else:
                apolar=apolar+1
        print polar, apolar, charged
        polar_percentage=float(polar)/len(self)
        apolar_percentage=float(apolar)/len(self)
        charged_percentage=float(charged)/len(self)
        return [polar_percentage, apolar_percentage, charged_percentage]

    def calculate_BSA(self):
        "Uses NACCESS module in order to calculate the Buried Surface Area"
        chains=[]
        nacc_at=NACCESS_atomic(self.model)

        sas_tot=0.0

        for at in self.model.get_atoms():
        # JR: Ignore Hydrogens otherwise NACCESS freaks out
        # See comment above
            if at.get_parent().id[0] == ' ' and at.element != 'H':
                sas_tot=sas_tot+float(at.xtra['EXP_NACCESS'])

        print 'Accessible surface area, complex:', sas_tot
        
        from Bio.PDB.Model import Model
        from Bio.PDB.Structure import Structure
        structure_A=Structure("chainA")
        structure_B=Structure("chainB")
        mA = Model(0)
        mB = Model(0)
        for c in self.get_chains():
            chains.append(c)

        mA.add(self.model[chains[0]])
        mB.add(self.model[chains[1]])
        structure_A.add(mA)
        structure_B.add(mB)
        print structure_A
        print structure_B
        #sys.exit()

        nacc_at=NACCESS_atomic(structure_A[0])
        nacc_at=NACCESS_atomic(structure_B[0])

        sas_A=0.0

        for at in structure_A.get_atoms():
            if at.get_parent().id[0] == ' '  and at.element != 'H':
                sas_A=sas_A+float(at.xtra['EXP_NACCESS'])

        print 'Accessible surface aream CHAIN A :', sas_A

        sas_B=0.0

        for at in structure_B.get_atoms():
            if at.get_parent().id[0] == ' '  and at.element != 'H':
                sas_B=sas_B+float(at.xtra['EXP_NACCESS'])

        print 'Accessible surface aream CHAIN B :',sas_B
        
        BSA=(sas_A+sas_B-sas_tot)
        
        print 'BSA =', BSA
        
        return BSA

