# CPAC/network_centrality/network_centraliy.py
#
# Authors: Daniel Clark

'''
This module contains functions which build and return the network
centrality nipype workflow
'''

# Import packages
from nipype.interfaces.base import (CommandLine, CommandLineInputSpec,
                                    TraitedSpec)

# Input spec class
class afniDegreeCentralityInputSpec(CommandLineInputSpec):
    '''
    '''

    # Import packages
    from nipype.interfaces.base import traits, File

    # Define class variables
    prefix = traits.Str(exists=True, argstr='-prefix %s', position=0,
                        desc='Output file name prefix', mandatory=True)
    mask = File(argstr='-mask %s', exists=True, position=1,
                desc='Mask file to use on input data')
    thresh = traits.Float(argstr='-thresh %f', position=2,
                          desc='Threshold to exclude where corr <= thresh')
    sparsity = traits.Float(argstr='-sparsity %f', position=3,
                            desc='The percentage of correlations to keep')
    out_1d = traits.Str(argstr='-out1D %s', position=4,
                        desc='Filepath to output 1D file with similarity matrix')
    polort = traits.Int(argstr='-polort %d', position=5,
                        desc='')
    autoclip = traits.Bool(argstr='-autoclip', desc='Clip off low-intensity '\
                                                    'regions in the dataset')
    automask = traits.Bool(argstr='-automask', desc='Mask the dataset to target '\
                                                    'brain-only voxels')


# Output spec class
class afniDegreeCentralityOutputSpec(TraitedSpec):
    '''
    '''

    # Import packages
    from nipype.interfaces.base import File

    # Define command outputs
    degree_outfile = File(desc='The binarized and weighted degree centrality '\
                               'images stored in two sub-briks of a nifti',
                          exists=True)
    one_d_outfile = File(desc='The text output of the similarity matrix computed'\
                             'after thresholding with one-dimensional and '\
                             'ijk voxel indices, correlations, image extents, '\
                             'and affine matrix')


# Command line execution class
class afniDegreeCentrality(CommandLine):
    '''
    '''

    # Define command, input, and output spec
    _cmd = '3dDegreeCentrality'
    input_spec = afniDegreeCentralityInputSpec
    output_spec = afniDegreeCentralityOutputSpec

    # Gather generated outputs
    def _list_outputs(self):

        # Import packages
        import os

        # Get generated outputs dictionary and assign generated outputs
        # to out output spec
        outputs = self.output_spec().get()
        outputs['degree_outfile'] = os.path.abspath(self.inputs.prefix)
        if self.inputs.out_1d:
            outputs['one_d_outfile'] = os.path.abspath(self.inputs.out_1d)

        # Return outputs
        return outputs


# Calculate eigenvector centrality from one_d file
def calc_eigen_from_1d(one_d_file, num_threads=1):
    '''
    '''

    # Import packages
    import os


# Return the network centrality workflow
def create_network_centrality_wf(wf_name='network_centrality', num_threads=1,
                                 memory=1, run_eigen=False):
    '''
    '''

    # Import packages
    import nipype.pipeline.engine as pe
    import nipype.interfaces.utility as util

    # Init variables
    centrality_wf = pe.Workflow(name='afni_centrality')

    # Define main input/function node
    afni_centrality_node = \
        pe.Node(interface=afniDegreeCentrality(environ={'OMP_NUM_THREADS' : num_threads}),
                name='afni_degree_centrality')

    # Limit its num_threads and memory via ResourceMultiProc plugin
    afni_centrality_node.interface.num_threads = num_threads
    afni_centrality_node.interface.memory = memory

    # Define outputs node
    output_node = \
        pe.Node(interface=util.IdentityInterface(fields=['degree_output',
                                                         'eigen_output',
                                                         'one_d_output']),
                name='output_node')

    # If run_eigen is set, connect 1d output to run_eigen node
    if run_eigen:
        # Tell 3dDegreeCentrality to create 1D file
        afni_centrality_node.inputs.out_1d = 'similarity_matrix.1D'

        # Init run eigenvector centrality node
        run_eigen_node = \
            pe.Node(interface=util.Function(input_names=['one_d_file',
                                                         'num_threads'],
                                            output_names=['eigen_outfile'],
                                            function=calc_eigen_from_1d),
                    name='run_eigen_node')
        # And pass in the number of threads for it to use
        run_eigen_node.inputs.num_threads = num_threads

        # Limit its num_threads and memory via ResourceMultiProce plugin
        run_eigen_node.interface.num_threads = num_threads
        run_eigen_node.interface.memory = memory

        # Connect in the run eigenvector node to the workflow 
        centrality_wf.connect(afni_centrality_node, 'one_d_outfile',
                              run_eigen_node, 'one_d_file')
        centrality_wf.connect(run_eigen_node, 'eigen_outfile',
                              output_node, 'eigen_output')

    # Connect the degree centrality outputs to output_node
    centrality_wf.connect(afni_centrality_node, 'degree_outfile',
                          output_node, 'degree_output')
    centrality_wf.connect(afni_centrality_node, 'one_d_outfile',
                          output_node, 'one_d_output')