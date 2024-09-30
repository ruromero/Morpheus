FROM registry.redhat.io/rhel9/python-311:latest

USER root

RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.rpm.sh | bash

RUN yum install -y git-lfs
