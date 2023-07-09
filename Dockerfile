FROM ubuntu:latest
RUN apt-get update && apt-get -y install build-essential git
RUN apt-get -y install opam --no-install-recommends
COPY packages /repo/packages
RUN opam init --disable-sandboxing /repo -an --bare
RUN opam switch create default --empty
RUN opam install -y dev-node dev-github-cli dev-rust.1.69 dev-rust-profile.minimal -v
