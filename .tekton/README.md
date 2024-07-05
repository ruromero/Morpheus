# Incremental build

## Prerequisite

First create the build-config to create a container image that has:

* Python 3.11 installed
* Git
* Git LFS

This image will be used in the preparation step.

## Preparation task

The first step of the pipeline will do the following preparation tasks:

1. Cleans up the possible previous data
1. Clone the git repository
1. Add the upstream repository
1. Fetch all the tags
1. Execute the `./docker/build_container_release.sh` script

Considerations:

* The Git tasks are necessary because the script requires some `git` commands to work and
it needs the closest tag. If we only clone with `depth=1` the closest tag will not be available.
Also if cloning from a fork, you might not have tags either. That's why we also add the remote.

* The build script has been updated so that the `docker build` is not executed but just echo-ed.
The build will take place in the next step

## Build task

Using buildah, we take most of the build arguments shown in the previous step output to configure
the Buildah build.
