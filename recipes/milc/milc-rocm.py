"""
MILC[develop] app: su3_rhmd_hisq 

Contents:
  Ubuntu 20.04 (LTS)
  ROCM 4.5.2
  GNU compilers (upstream; 9.3.0)
  OFED Mellanox 5.4-1.0.3.0 (ConnectX gen 4--6)
  OpenMPI version 4.1.2
  Quda version feature/hip-compile-fixes
"""

# pylint: disable=invalid-name, undefined-variable, used-before-assignment
# pylama: ignore=E0602

# command line options
gpu_arch = USERARG.get('GPU_ARCH', 'gfx908')
use_ucx  = USERARG.get('ucx', None) is not None

base_distro = 'ubuntu20'
devel_image   = 'rocm/dev-ubuntu-20.04:4.5.2-complete'
runtime_image = 'library/ubuntu:20.04'

# add docstring to Dockerfile
Stage0 += comment(__doc__.strip(), reformat=False)

###############################################################################
# Devel stage
###############################################################################
Stage0 += baseimage(image=devel_image, _distro=base_distro, _as='devel')

# required packages
Stage0 += packages(ospackages=[],
                   apt=['wget', 'autoconf', 'automake', 'ca-certificates', 'git', 'locales',
                        'libgmp-dev', 'libmpfr-dev', 'libssl-dev', 'libnuma-dev' ],
                   yum=['wget', 'autoconf', 'automake', 'ca-certificates', 'git',
                        'gmp-devel',   'mpfr-devel', 'openssl-devel', 'numactl-devel', ])

# cmake
Stage0 += cmake(eula=True, version='3.22.2')

# GNU compilers
compiler = gnu()
Stage0 += compiler

# Mellanox OFED
Stage0 += mlnx_ofed(version='5.4-1.0.3.0')

# OpenMPI
if use_ucx:
    # UCX depends on KNEM (use latest versions as of 2022-01-22)
    Stage0 += knem(version='1.1.4')
    Stage0 += ucx(cuda=False, version='1.12.0')
    pass

Stage0 += openmpi(version='4.1.2',
               cuda=False,
               ucx=use_ucx, infiniband=not use_ucx,
               toolchain=compiler.toolchain)

if not use_ucx:
    Stage0 += shell(commands=[
        'echo "btl_openib_allow_ib = 1" >> /usr/local/openmpi/etc/openmpi-mca-params.conf'])

# build xthi
Stage0 += generic_build(branch='master',
                        build=['make all CC=gcc MPICC=/usr/local/openmpi/bin/mpicc', ],
                        install=['mkdir -p /usr/local/xthi/bin',
                                 'cp /var/tmp/xthi/xthi /var/tmp/xthi/xthi.nompi /usr/local/xthi/bin'],
                        prefix='/usr/local/xthi',
                        repository='https://git.ecdf.ed.ac.uk/dmckain/xthi.git')
Stage0 += environment(variables={'PATH': '/usr/local/xthi/bin:$PATH'})

# fix locale to stop perl from complaining
Stage0 += shell(commands=[ 'locale-gen en_US', 'locale-gen en_US.UTF-8', 'update-locale LC_ALL=en_US.UTF-8',])

# build QUDA
# AMD gpus and llvm  https://llvm.org/docs/AMDGPUUsage.html#processors
# MI100:  gfx908  "Arcturis": gfx90a
if True:
    Stage0 += generic_cmake(branch='feature/hip-compile-fixes',
                            build_environment={
                                'QUDA_GPU_ARCH': 'gfx908',
                            },
                            cmake_opts=['-DCMAKE_BUILD_TYPE=RELEASE',
                                        '-DCMAKE_CXX_COMPILER=hipcc',
                                        '-DCMAKE_C_COMPILER=hipcc',
                                        '-DCMAKE_C_STANDARD=99',
                                        '-DMPI_CXX_COMPILER=mpicxx',
                                        '-DBUILD_TESTING=ON',
                                        '-DQUDA_OPENMP=OFF',
                                        '-DQUDA_MAX_MULTI_BLAS_N=9',
                                        '-DQUDA_BUILD_SHAREDLIB=ON',
                                        '-DQUDA_DIRAC_DEFAULT_OFF=ON',
                                        '-DQUDA_DIRAC_STAGGERED=ON',
                                        '-DQUDA_DIRAC_WILSON=ON',
                                        '-DQUDA_DOWNLOAD_USQCD=ON',
                                        '-DQUDA_FORCE_GAUGE=ON',
                                        '-DQUDA_FORCE_HISQ=ON',
                                        '-DQUDA_INTERFACE_MILC=ON',
                                        '-DQUDA_INTERFACE_QDP=ON',
                                        '-DQUDA_MPI=OFF',
                                        '-DQUDA_QIO=ON',
                                        '-DQUDA_QMP=ON',
                                        '-DROCM_PATH=/opt/rocm-4.5.2',
                                        '-Dhip_DIR=/opt/rocm-4.5.2/hip/lib/cmake/hip',
                                        '-Dhipfft_DIR=/opt/rocm-4.5.2/hipfft/lib/cmake/hipfft',
                                        '-DAMDDeviceLibs_DIR=/opt/rocm-4.5.2/lib/cmake/AMDDeviceLibs',
                                        '-Damd_comgr_DIR=/opt/rocm-4.5.2/lib/cmake/amd_comgr',
                                        '-Dhsa-runtime64_DIR=/opt/rocm-4.5.2/lib/cmake/hsa-runtime64',
                                        '-Dhiprand_DIR=/opt/rocm-4.5.2/hiprand/lib/cmake/hiprand',
                                        '-Drocrand_DIR=/opt/rocm-4.5.2/rocrand/lib/cmake/rocrand',
                                        '-Dhipblas_DIR=/opt/rocm-4.5.2/hipblas/lib/cmake/hipblas',
                                        '-Drocblas_DIR=/opt/rocm-4.5.2/rocblas/lib/cmake/rocblas',
                                        '-Dhipcub_DIR=/opt/rocm-4.5.2/hipcub/lib/cmake/hipcub',
                                        '-Drocprim_DIR=/opt/rocm-4.5.2/rocprim/lib/cmake/rocprim',
                                        '-DGPU_TARGETS=gfx908',
                                        '-DQUDA_TARGET_TYPE=HIP',
                                    ],
                            install=True,
                            ldconfig=False,
                            runtime=[
                                '/usr/local/quda',
                            ],
                            prefix='/usr/local/quda',
                            repository='https://github.com/lattice/quda.git')

    pass

# build MILC
milc_opts = [
    'PRECISION=2',
    'OMP=true',
    'MPP=true',
    'CC=/usr/local/openmpi/bin/mpicc',
    'CXX=/usr/local/openmpi/bin/mpicxx',
    'LD=/usr/local/openmpi/bin/mpicxx',
    'WANTQMP=true',
    'WANTQIO=true',
    'CTIME="-DCGTIME -DFFTIME -DGFTIME -DFLTIME -DPRTIME"',
    'QMPPAR=/usr/local/quda',
    'QIOPAR=/usr/local/quda',
    'LIBSCIDAC="-Wl,-rpath=/usr/local/quda/lib -L/usr/local/quda/lib -lqmp -lqio -llime"',]
milc_gpu = [
    'CUDA_HOME=/opt/rocm-4.5.2',
    'QUDA_HOME=/usr/local/quda',
    'LD_FLAGS="-L/usr/local/cuda/lib64 -Wl,-rpath=/usr/local/cuda/lib64"',
    'LIBQUDA="-Wl,-rpath=/usr/local/quda/lib -L/usr/local/quda/lib -llime -lquda"',
    'WANTQUDA=true',
    'WANT_MIXED_PRECISION_GPU=1',
    'WANT_CL_BCG_GPU=true',
    'WANT_FN_CG_GPU=true',
    'WANT_FL_GPU=true',
    'WANT_FF_GPU=true',
    'WANT_GF_GPU=true',]
# TODO: 'CGEOM=-DFIX_NODE_GEOM', # add prompt to specify lattice partitioning?

# build both CPU and GPU-accelerated versions
Stage0 += generic_build(branch='develop',
                        build=['cp Makefile ks_imp_rhmc',
                               'cd ks_imp_rhmc',
                               'make -j 1 su3_rhmd_hisq ' + ' '.join(milc_opts),
                               'mv su3_rhmd_hisq su3_rhmd_hisq_cpu',
                               'make clean', 'rm -f .lastmake* localmake',
                               'cd ../libraries', 'make -f Make_vanilla clean', 'cd ../ks_imp_rhmc',
                               'make -j 1 su3_rhmd_hisq ' + ' '.join(milc_opts) + ' ' + ' '.join(milc_gpu),],
                        install=['mkdir -p /usr/local/milc/bin',
                                 'cp /var/tmp/milc_qcd/ks_imp_rhmc/su3_rhmd_hisq      /usr/local/milc/bin',
                                 'cp /var/tmp/milc_qcd/ks_imp_rhmc/su3_rhmd_hisq_cpu  /usr/local/milc/bin',],
                        prefix='/usr/local/milc',
                        repository='https://github.com/milc-qcd/milc_qcd')
Stage0 += environment(variables={'PATH': '/usr/local/milc/bin:$PATH'})


###############################################################################
# Release stage
###############################################################################
# centos8 /etc/yum.repos.d/rocm.repo
rocm_centos8 = """
[rocm]
name=rocm
baseurl=https://repo.radeon.com/rocm/centos8/4.5.2/
enabled=1
gpgcheck=1
gpgkey=https://repo.radeon.com/rocm/rocm.gpg.key
"""

Stage1 += baseimage(image=runtime_image, _distro=base_distro)

Stage1 += packages(ospackages=[ 'wget', 'gnupg2', 'ca-certificates',])

# libnuma.so.1 needed by xthi
Stage1 += packages(apt=['libmpfr6', 'libgmp10', 'libnuma1'],yum=['mpfr', 'gmp', 'numactl-libs',])

# ubuntu add rocm repo
if base_distro == 'ubuntu20':
    Stage1 += shell(commands=[
        'wget -q -O - https://repo.radeon.com/rocm/rocm.gpg.key | apt-key add -',
        'echo \'deb [arch=amd64] https://repo.radeon.com/rocm/apt/4.5.2/ ubuntu main\' | tee /etc/apt/sources.list.d/rocm.list',])
elif base_distro == 'centos8':
    Stage1 += shell(commands=[
        'mkdir -p /etc/yum.repos.d/',
        'echo "' + rocm_centos8 + '" > /etc/yum.repos.d/rocm.repo', ])
    pass

# rocm runtime
Stage1 += packages(ospackages=[ 'rocm-language-runtime', 'rocm-hip-runtime', 'rocm-opencl-runtime', 'rocm-hip-libraries', ])

# copy runtime libomp
d = '/opt/rocm-4.5.2/llvm/lib/'
Stage1 += copy(_from='devel',src= [d+'libomp.so', d+'libompstub.so', d+'libomptarget.rtl.amdgpu.so', d+'libomptarget.rtl.x86_64.so', d+'libomptarget.so', ],
               dest=d)

Stage1 += Stage0.runtime()

Stage1 += environment(variables={
    'PATH': '/usr/local/milc/bin:/usr/local/quda/bin:/usr/local/xthi/bin:$PATH',
    'LD_LIBRARY_PATH': '/usr/local/quda/lib:$LD_LIBRARY_PATH', })
