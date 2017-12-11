# -*- coding: utf-8 -*-
"""
General description:
---------------------
Example from the SDEWES conference paper:

Simon Hilpert, Cord Kaldemeyer, Uwe Krien, Stephan Günther (2017).
'Solph - An Open Multi Purpose Optimisation Library for Flexible
         Energy System Analysis'. Paper presented at SDEWES Conference,
         Dubrovnik.

Installation requirements:
---------------------------
This example requires the latest version of oemof. Install by:

    pip install oemof

"""
import os
import pandas as pd

from oemof.network import Node
from oemof.outputlib.graph_tools import graph
from oemof.outputlib import processing
from oemof.solph import (EnergySystem, Bus, Source, Sink, Flow, NonConvex,
                         Model, Transformer, components)

timeindex = pd.date_range('1/1/2017', periods=168, freq='H')

energysystem = EnergySystem(timeindex=timeindex)
Node.registry = energysystem
##########################################################################
# data
##########################################################################
# Read data file
full_filename = os.path.join(os.path.dirname(__file__),
                             'timeseries.csv')
timeseries = pd.read_csv(full_filename, sep=',')


##########################################################################
# Create oemof object
##########################################################################

bel = Bus(label='bel')

Sink(label='demand_el',
     inputs={
         bel: Flow(actual_value=timeseries['demand_el'],
                   fixed=True, nominal_value=100)})

Source(label='pp_wind',
       outputs={
           bel: Flow(nominal_value=40, fixed=True,
                     actual_value=timeseries['wind'])})

Source(label='pp_pv',
       outputs={
           bel: Flow(nominal_value=20, fixed=True,
                     actual_value=timeseries['pv'])})

Source(label='pp_gas',
       outputs={
           bel: Flow(nominal_value=50, nonconvex=NonConvex(),
                     variable_costs=60,
                     negative_gradient={'ub': 0.05, 'costs': 0},
                     positive_gradient={'ub': 0.05, 'costs': 0})})

Source(label='pp_bio',
       outputs={
           bel: Flow(nominal_value=5,
                     variable_costs=100)})

components.GenericStorage(
    label='storage_el',
    inputs={
        bel: Flow()},
    outputs={
        bel: Flow()},
    nominal_capacity=40,
    nominal_input_capacity_ratio=1/10,
    nominal_output_capacity_ratio=1/10,
)

# heat componentes
bth = Bus(label='bth')

bgas = Bus(label='bgas')

Source(label='gas',
       outputs={
           bgas: Flow()})


Sink(label='demand_th',
     inputs={
         bth: Flow(actual_value=timeseries['demand_th'],
                   fixed=True, nominal_value=100)})

Transformer(label='pth',
            inputs={
                bel: Flow()},
            outputs={
                bth: Flow(nominal_value=30)},
            conversion_factors={bth: 0.99})

Transformer(label='chp',
            inputs={
                bgas: Flow(variable_costs=80)},
            outputs={
                 bel: Flow(nominal_value=40),
                 bth: Flow()},
            conversion_factors={bel: 0.4,
                                bth: 0.4})

Source(label='boiler_bio',
       outputs={
           bth: Flow(nominal_value=100,
                     variable_costs=60)})

components.GenericStorage(
    label='storage_th',
    inputs={
        bth: Flow()},
    outputs={
        bth: Flow()},
    nominal_capacity=30,
    nominal_input_capacity_ratio=1/8,
    nominal_output_capacity_ratio=1/8,
)

##########################################################################
# Create model and solve
##########################################################################

m = Model(energysystem)
# emission_limit(m, flows=m.flows, limit=954341)

m.write('test_nc.lp', io_options={'symbolic_solver_labels': True})

m.solve(solver='cbc', solve_kwargs={'tee': True})

results = processing.results(m)


graph = graph(energysystem, m, plot=True, layout='neato', node_size=3000,
              node_color={'bel': '#7EC0EE', 'bgas': '#eeac7e', 'bth': '#cd3333'})
