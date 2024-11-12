# Notes about the ci build

## The pipeline

The pipeline has 2 steps.

1. Prepare the build: Mainly what the [build_container_release.sh](../docker/build_container_release.sh) script does but considering the possibility of running from a fork.
At the end of the script will `echo` the docker command that is expected to be executed (for debugging)
1. Executes a custom [buildah task](./buildah-task-persistent.yaml) but with some peculiarities:
    1. It pushes intermediate layers to the local registry (for incremental builds)
    1. It persists the varlibcontainers because the ephemeral storage is not enough for this build. The build requires a huge amount of disk (over 600Gi)

At the end, the build should push the resulting image to the configured repository.

## Registry authentication

The pipeline interacts with up to 3 different registries:

* Quay.io/ecosystem-appeng/[morpheus|agent-morpheus-rh/agent-morpheus-client]. To push the builds to the specific repository.
* Red Hat registry. To pull Red Hat images. Mainly for the AgentMorpheus Client
* Internal openshift registry (optional) for caching layers. Althoug it's not really needed but useful when you need to do incremental builds

Create a config.json file with the contents of:
* The auth for the quay.io service account with push access to these registries
* The service account credentials for the RH registry
* The base64 decoded content of the pipeline secret -> for the openshift registry (e.g. pipeline-dockercfg-99svh)

Example:


```json
{
  "auths": {
    "quay.io": {
      "auth": "........."
    },
    "registry.redhat.io": {
      "auth": "........."
    },
    "172.30.151.0:5000": {
      "auth": "........."
    },
    "default-route-openshift-image-registry.apps.ai-dev03.kni.syseng.devcluster.openshift.com": {
      "auth": "........."
    },
    "image-registry.openshift-image-registry.svc.cluster.local:5000": {
      "auth": "........."
    },
    "image-registry.openshift-image-registry.svc:5000": {
      "auth": "........."
    }
  }
}
```

Create the secret from this file:

```bash
oc create secret generic morpheus-build-buildah-secret --from-file=config.json
```

Reference this secret in the [pipelinerun](./pipelinerun.yaml)

## Create the pipeline resources

* Create the custom buildah task
* Create the pipeline (with layers only if you need to debug intermediate steps)

```bash
oc apply -f .tekton/buildah-task-persistent.yaml
oc apply -f .tekton/morpheus-incremental.yaml
```

## Create the pipeline run

We use 2 PVC templates, one of 1Gi for the sources and another one to store the intermediate layers during build.
The second one needs to be very big (over 800Gi) due to the big size of the layers and the number of intermediate
steps.

```bash
oc create -f .tekton/pipelinerun.yaml
```