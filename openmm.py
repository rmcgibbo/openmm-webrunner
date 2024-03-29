##########################################################################
# this script was generated by openmm-builder. to customize it further,
# you can save the file to disk and edit it with your favorite editor.
##########################################################################

from __future__ import print_function
from simtk.openmm.app import *
from simtk.openmm import *
from simtk.unit import *
from sys import stdout

pdb = PDBFile('input.pdb')
forcefield = ForceField('amber99sbildn.xml', 'tip3p.xml')

system = forcefield.createSystem(pdb.topology, nonbondedMethod=PME, 
    nonbondedCutoff=1.0*nanometers, constraints=HBonds, rigidWater=True, 
    ewaldErrorTolerance=0.0005)
integrator = LangevinIntegrator(300*kelvin, 1.0/picoseconds, 2.0*femtoseconds)
integrator.setConstraintTolerance(0.00001)

platform = Platform.getPlatformByName('CUDA')
properties = {'CudaPrecision': 'mixed'}
simulation = Simulation(pdb.topology, system, integrator, platform, properties)
simulation.context.setPositions(pdb.positions)

print('Minimizing...')
simulation.minimizeEnergy()

simulation.context.setVelocitiesToTemperature(300*kelvin)
print('Equilibrating...')
simulation.step(100)

simulation.reporters.append(DCDReporter('output.dcd', 1000))
simulation.reporters.append(StateDataReporter(stdout, 1000, step=True, 
    potentialEnergy=True, temperature=True))

print('Running Production...')
simulation.step(1000)
print('Done!')
