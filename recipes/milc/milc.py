"""
MILC[develop] app: su3_rhmd_hisq 

Contents:
  Ubuntu 20.04 (LTS)
  CUDA version 11.6
  GNU compilers (upstream; 9.3.0)
  OFED Mellanox 5.4-1.0.3.0 (ConnectX gen 4--6)
  OpenMPI version 4.1.2
  QUDA version develop
"""

# pylint: disable=invalid-name, undefined-variable, used-before-assignment
# pylama: ignore=E0602

# command line options
gpu_arch = USERARG.get('GPU_ARCH', 'sm_70')
use_ucx  = USERARG.get('ucx', None) is not None

devel_image   = 'nvcr.io/nvidia/cuda:11.6.0-devel-ubuntu20.04'
runtime_image = 'nvcr.io/nvidia/cuda:11.6.0-base-ubuntu20.04'

# add docstring to Dockerfile
Stage0 += comment(__doc__.strip(), reformat=False)

###############################################################################
# Devel stage
###############################################################################
Stage0 += baseimage(image=devel_image, _as='devel')

# GNU compilers
compiler = gnu()
Stage0 += compiler

# Mellanox OFED
Stage0 += mlnx_ofed(version='5.4-1.0.3.0')

# OpenMPI
if use_ucx:
    # UCX depends on KNEM (use latest versions as of 2022-01-22)
    Stage0 += knem(version='1.1.4')
    Stage0 += ucx(cuda=True, version='1.12.0')
    pass

Stage0 += openmpi(version='4.1.2',
                  cuda=True,
                  ucx=use_ucx, infiniband=not use_ucx,
                  toolchain=compiler.toolchain)

if not use_ucx:
    Stage0 += shell(commands=[
        'echo "btl_openib_allow_ib = 1" >> /usr/local/openmpi/etc/openmpi-mca-params.conf'])

# cmake and git
Stage0 += cmake(eula=True, version='3.22.2')
Stage0 += packages(ospackages=['ca-certificates', 'git'])

# build xthi
Stage0 += generic_build(branch='master',
                        build=['make all CC=gcc MPICC=/usr/local/openmpi/bin/mpicc', ],
                        install=['mkdir -p /usr/local/xthi/bin',
                                 'cp /var/tmp/xthi/xthi /var/tmp/xthi/xthi.nompi /usr/local/xthi/bin'],
                        prefix='/usr/local/xthi',
                        repository='https://git.ecdf.ed.ac.uk/dmckain/xthi.git')
Stage0 += environment(variables={'PATH': '/usr/local/xthi/bin:$PATH'})

# build QUDA
Stage0 += generic_cmake(branch='develop',
                        cmake_opts=['-DCMAKE_BUILD_TYPE=RELEASE',
                                    '-DBUILD_TESTING=ON',
                                    '-DQUDA_BUILD_SHAREDLIB=ON',
                                    '-DQUDA_DIRAC_CLOVER=OFF',
                                    '-DQUDA_DIRAC_CLOVER_HASENBUSCH=OFF',
                                    '-DQUDA_DIRAC_DOMAIN_WALL=OFF',
                                    '-DQUDA_DIRAC_NDEG_TWISTED_CLOVER=OFF',
                                    '-DQUDA_DIRAC_NDEG_TWISTED_MASS=OFF',
                                    '-DQUDA_DIRAC_STAGGERED=ON',
                                    '-DQUDA_DIRAC_TWISTED_CLOVER=OFF',
                                    '-DQUDA_DIRAC_TWISTED_MASS=OFF',
                                    '-DQUDA_DIRAC_WILSON=ON',
                                    '-DQUDA_DOWNLOAD_USQCD=ON',
                                    '-DQUDA_FORCE_GAUGE=ON',
                                    '-DQUDA_FORCE_HISQ=ON',
                                    '-DQUDA_GPU_ARCH={}'.format(gpu_arch),
                                    '-DQUDA_INTERFACE_MILC=ON',
                                    '-DQUDA_INTERFACE_QDP=ON',
                                    '-DQUDA_MPI=OFF',
                                    '-DQUDA_QIO=ON',
                                    '-DQUDA_QMP=ON',
                                    '-DQUDA_TARGET_TYPE=CUDA',
                                ],
                        install=True,
                        ldconfig=False,
                        runtime=[
                            '/usr/local/quda',
                            '/usr/local/cuda-11.6/targets/x86_64-linux/lib/libcublas{,Lt}.so.11.*',
                        ],
                        prefix='/usr/local/quda',
                        repository='https://github.com/lattice/quda.git')


Stage0 += environment(variables={
    'PATH': '/usr/local/quda/bin:$PATH',
    'LD_LIBRARY_PATH': '/usr/local/quda/lib:$LD_LIBRARY_PATH', })

# build MILC
if True:
    milc_opts = [
        'PRECISION=2',
        'OMP=true',
        'MPP=true',
        'CC=/usr/local/openmpi/bin/mpicc',
        'CXX=/usr/local/openmpi/bin/mpicxx',
        'LD=/usr/local/openmpi/bin/mpicxx',
        'QUDA_HOME=/usr/local/quda',
        'LD_FLAGS="-L/usr/local/cuda/lib64 -Wl,-rpath=/usr/local/cuda/lib64"',
        'WANTQUDA=true',
        'WANT_MIXED_PRECISION_GPU=2',
        'WANT_CL_BCG_GPU=true',
        'WANT_FN_CG_GPU=true',
        'WANT_FL_GPU=true',
        'WANT_FF_GPU=true',
        'WANT_GF_GPU=true',
        'WANTQMP=true',
        'WANTQIO=true',
        'QMPPAR=/usr/local/quda',
        'QIOPAR=/usr/local/quda',
    ]

    Stage0 += generic_build(branch='develop',
                            build=['cp Makefile ks_imp_rhmc',
                                   'cd ks_imp_rhmc',
                                   'make -j 1 su3_rhmd_hisq ' + ' '.join(milc_opts), ],
                            install=['mkdir -p /usr/local/milc/bin',
                                     'cp /var/tmp/milc_qcd/ks_imp_rhmc/su3_rhmd_hisq /usr/local/milc/bin'],
                            prefix='/usr/local/milc',
                            repository='https://github.com/milc-qcd/milc_qcd')
    Stage0 += environment(variables={'PATH': '/usr/local/milc/bin:$PATH'})
    pass

###############################################################################
# Release stage
###############################################################################
Stage1 += baseimage(image=runtime_image)

Stage1 += Stage0.runtime()

# libnuma.so.1 needed by xthi
Stage1 += packages(apt=['libnuma1'],yum=['numactl-libs',])

Stage1 += environment(variables={
    'PATH': '/usr/local/milc/bin:/usr/local/quda/bin:/usr/local/xthi/bin:$PATH',
    'LD_LIBRARY_PATH': '/usr/local/quda/lib:/usr/local/cuda/lib64:$LD_LIBRARY_PATH', })
