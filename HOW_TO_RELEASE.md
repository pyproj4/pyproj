# Preparing a pyproj release

Preparing a pyproj release is a two-phase process.

## Phase 1: Release Candidate

In this phase, we want to ensure all the builds work on all platforms and methods
of distribution for the next release.

### Add the rc postfix

The first step in this phase is to update the version number `__version__` in `__init__.py`
to the next release `<major>.<minor>.<patch>`. Then, add the `rc` style posfix following the [PEP-440](https://www.python.org/dev/peps/pep-0440/#pre-releases) conventions.

### Create a tag on the repository

The next step is to create a tag with the same name as the version just added. This can be done using the git command line or from https://github.com/pyproj4/pyproj/tags.

### Test the release builds

1. Check the wheels built at https://github.com/pyproj4/pyproj using GitHub Actions.
2. Create a draft PR at https://github.com/conda-forge/pyproj-feedstock and verify tests pass.
3. Verify Debian builds were successful.
4. Verify Fedora builds were successful.
5. Verify the docs build successfully.

## Phase 2: Make the release

After the candidate has proven itself, it will be promoted to a final release.

### Remove the rc postfix

Remove the `rc` postfix from the the version number `__version__` in `__init__.py`.

### Create a tag on the repository

The next step is to create a tag with the name `<major>.<minor>.<patch>`. This can be done using the git command line or from https://github.com/pyproj4/pyproj/tags.

Next, go through the history and add release notes (see: [automatically generated release notes](https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes)). Make sure to acknowledge contributions made by others in the release.

### The wheels

The wheels are tested with each merge to main and uploaded to https://pypi.anaconda.org/scientific-python-nightly-wheels/simple in GitHub Actions. They are uploaded to pypi on pre-release and release in GitHub Actions.

### Verify conda-forge build is correct

A PR for `pyproj` will be generated automatically after you push to pypi.
Verify all is correct on the PR at https://github.com/conda-forge/pyproj-feedstock.

### Update the docs

On the `gh-pages` branch, update the stable symlink to point to the next version.
