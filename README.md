# Depending on multiple programming language toolchains with opam

This repository solves the problem of how to depend on multiple non-OCaml
toolchains (e.g. Python or Rust) from the opam repository.

## Multi-language devcontainer package repository

[Devcontainers](https://containers.dev) are an emerging mechanism to use
container runtimes as a full-fledged development environment.  They
can support multiple programming languages in one filesystem by means
of [features](https://containers.dev/implementors/features/), which allow
for the activation of a given toolchain alongside others. For example,
using features allows for the simultaneous use of Python, Rust and OCaml
within one container image, whereas with traditional devcontainers there
would be a separate container for each toolchain.

## Using the opam solver to manage feature selection

The [opam](https://opam.ocaml.org) package manager integrates a builtin
constraint solver that allows for the selection of a compatible set of
dependencies from a package repository that contains all released versions
of all packages.

This repository translates published devcontainers into opam packages, such
that devcontainer features can be selected by simply adding dependencies
to an opam package.  Additionally, version constraints on the desired
tooling can be added to pick the required versions. For example:

```
depends: [ "dev-rust" {>="1.68"}
           "dev-ocaml" {>="4.12" & < "5.0"}
           "dev-python"
           "dev-python-optimize" ]
```

This picks a version of Rust greater than 1.68, and any OCaml compiler
between 4.12-4.14, and any Python compiler with the `optimize` flag
activated for more efficient code generation.

## The Good News

This solution frees the opam-repo maintainers from having to support the
myriad other toolchains, and lets us depend on them freely from opam.
By adding explicit dependencies like this, we can continue to run
automated end-to-end tests for new and existing packages in the OCaml
ecosystem, even when they do not exclusively use OCaml.

## The Bad News

There are still some limitations to figure out before this is production
worthy:

- [ ] The devcontainer installation busts the opam security sandbox, and
  so cannot be installed simultaneously with normal packages.  It would be
  ok in a CI system where sandboxing is normally disabled.  Another option
  is for these packages to not actually perform the installation, but generate
  a single `install.sh` with all the right environment variables.  An image
  generator could then run that script to generate a base image.
- [ ] opam doesn't currently support composing remote repositories, so
  some strategy is needed for how to keep this generated repo in sync
  with anything included in the central repository.
- [ ] support devcontainer boolean defaults correctly (e.g. Python feature)
- [ ] figure out what to do about arbitrary string options. Env variables
  could be used to pass in values, but opam can't recompile if these
  variables change. Dune does support systematic env variable tracking
  and recompile if it changes, so this would work in a monorepo.
- [ ] something, something, Nix?
