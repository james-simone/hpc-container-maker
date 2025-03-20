# EESSI software container

The European Environment for Scientific Software Installations, [EESSI](https://www.eessi.io/docs/), is a collaboration between different European partners in HPC community.
The goal of the project is to build a common stack of scientific software installations for HPC systems and beyond, including laptops, personal workstations and cloud infrastructure.

The EESSI project leverages [EasyBuild](https://easybuild.io/) to build software packages and the [CernVM-fs](https://cvmfs.readthedocs.io/en/stable/) file system to distribute binary software to client systems.
See the [listing](https://www.eessi.io/docs/available_software/overview/) of architectures and software packages provided by EESSI.

## Run a Singularity image with Apptainer or Singularity

Create writable directories on the host that fuse-overlay will mount as `/var/lib/cvmfs` and `/var/run/cvmfs`.
```
mkdir -p /tmp/$USER/{var-lib-cvmfs,var-run-cvmfs}
```

`Exec` a login shell, `/bin/bash -l`, to setup `Lmod` software modules:
```
apptainer exec \
      --bind /tmp/simone/var-lib-cvmfs:/var/lib/cvmfs \
      --bind /tmp/simone/var-run-cvmfs:/var/run/cvmfs \
      --fusemount 'container:cvmfs2 cvmfs-config.cern.ch /cvmfs/cvmfs-config.cern.ch' \
      --fusemount 'container:cvmfs2 software.eessi.io /cvmfs/software.eessi.io' \
      eessi_client.sif /bin/bash -l
```

## Run a Docker image with Podman or Docker

Create writable directories on the host that fuse-overlay will mount as `/var/lib/cvmfs` and `/var/run/cvmfs`.
```
mkdir -p /tmp/$USER/{var-lib-cvmfs,var-run-cvmfs}
```

Run the container, tagged here `eessi_client`, with the command
```
podman run -v /tmp/$USER/var-lib-cvmfs:/var/lib/cvmfs \
           -v /tmp/$USER/var-run-cvmfs:/var/run/cvmfs \
           --device /dev/fuse --cap-add SYS_ADMIN \
	   -v $HOME:/work \
	   -it eessi_client
```

You must run the `cvmfs2` command inside the container to activate the CVMFS fuse mount
```
cvmfs2 cvmfs-config.cern.ch /cvmfs/cvmfs-config.cern.ch
cvmfs2 software.eessi.io /cvmfs/software.eessi.io
```
The EESSI software should now be listed in Lmod package management system with the command
```
module avail
```





