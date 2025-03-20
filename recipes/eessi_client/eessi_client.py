"""
Client container for the European Environment for Scientific Software Installations (EESSI) project.

The European Environment for Scientific Software Installations (EESSI,
pronounced as "easy") is a collaboration between different European
partners in HPC community. The goal of this project is to build a
common stack of scientific software installations for HPC systems and
beyond, including laptops, personal workstations and cloud
infrastructure.

See the [EESSI documentation](https://www.eessi.io/docs/) for details.

Software packages within the container are distributed via a FUSE mount /cvmfs/software.eessi.io/

"""

#pylint: disable=invalid-name, undefined-variable, used-before-assignment

# hpccm supports cpuarch in [ 'aarch64', 'ppc64le', 'x86_64' ]
# EESSI supports cpuarch in [ 'aarch64', 'x86_64' ] while 'riscv64' is under development

# base image RHEL-like distribution
osimage = 'almalinux:9'
distro = 'rockylinux9'

# version of FUSE overlayfs to install
fuseoverlayfsversion='1.14'

#TODO:
# create /etc/profile.d/z00_lmod.sh and /etc/profile.d/z00_lmod.csh adding /cvmfs/software.eessi.io/init/modules

Stage0 += baseimage(image=osimage,_as='final',_distro=distro)
Stage0 += packages(epel=True,yum=['sudo', 'vim', 'openssh-clients', 'lsof', 'strace', 'libibverbs', 'Lmod'])
Stage0 += packages(yum=['https://cvmrepo.s3.cern.ch/cvmrepo/yum/cvmfs-release-latest.noarch.rpm'])
Stage0 += packages(yum=['cvmfs','cvmfs-libs','cvmfs-config-default','cvmfs-fuse3'])
Stage0 += packages(yum=['https://github.com/EESSI/filesystem-layer/releases/download/latest/cvmfs-config-eessi-latest.noarch.rpm'])
Stage0 += shell(commands=[
    f'curl -L -o /usr/local/bin/fuse-overlayfs https://github.com/containers/fuse-overlayfs/releases/download/v{fuseoverlayfsversion}/fuse-overlayfs-$(uname -m)',
    'chmod +x-w /usr/local/bin/fuse-overlayfs',
    'echo \'CVMFS_QUOTA_LIMIT=10000\' > /etc/cvmfs/default.local',
    'echo \'CVMFS_CLIENT_PROFILE="single"\' >> /etc/cvmfs/default.local',
    'echo \'CVMFS_HIDE_MAGIC_XATTRS=yes\' >> /etc/cvmfs/default.local',
    'mkdir -p /cvmfs/cvmfs-config.cern.ch /cvmfs/software.eessi.io',
    'useradd -ms /bin/bash eessi',
    'echo \'export MODULEPATH=$(/usr/share/lmod/lmod/libexec/addto --append MODULEPATH /cvmfs/software.eessi.io/init/modules)\' > /etc/profile.d/z00_lmod.sh',
    'echo \'setenv MODULEPATH `/usr/share/lmod/lmod/libexec/addto --append MODULEPATH /cvmfs/software.eessi.io/init/modules`\' > /etc/profile.d/z00_lmod.csh'])
