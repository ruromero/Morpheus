FROM nvcr.io/nvidia/morpheus/morpheus:v24.03.02-runtime

USER root

RUN mamba env update \
  -n morpheus \
  --file ./conda/environments/all_cuda-121_arch-x86_64.yaml && \
  pip install debugpy

ENTRYPOINT ["sleep", "infinity"]