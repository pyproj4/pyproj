# Preparing a pyproj release

Preparing a pyproj release is a two-phase process.

## Phase 1: Release Candidate

In this phase, we want to ensure all the builds work on all platforms and methods
of distribution for the next release.

### Add the rc postfix

The first step in this phase is to update the version number `__version__` in `__init__.py`
to the next release `<major>.<minor>.<patch>`. Then, add the `rc` style posfix following the[PEP-440](https://www.python.org/dev/peps/pep-0440/#pre-releases)
conventions starting with `rc0` (ex. `3.7.2rc0`).

### Review changes in the changelog

Review `docs/history.rst` and compare to list of merged pull requests since the previous release:

https://github.com/pyproj4/pyproj/pulls?q=sort%3Aupdated-desc+is%3Apr+is%3Amerged

### Create a tag on the repository

The next step is to create a tag with the same name as the version just added. This can be done using the git command line.
Make sure you are on the `main` branch first. For example:

```bash
git checkout main
git tag 3.7.2rc0
```

This creates a lightweight git tag.

Push the tag to github with:

```bash
git push --follow-tags
```

### Create a GitHub Release

1. Go to https://github.com/pyproj4/pyproj/releases.
2. Click "Draft a new release".
3. Select the release candidate tag you just pushed from the "Select tag" dropdown list.
4. Enter "X.Y.Zrc0" as the Release title using the version number you created.
5. In the description enter "MNT: Version X.Y.Zrc0"
6. Check the box for "Set as a pre-release".
7. Check the box for "Create a discussion for this release".
8. Click "Publish release".

### Test the release builds

1. Check the wheels built at https://github.com/pyproj4/pyproj using GitHub Actions.
2. Verify wheel and sdist upload to PyPI at https://pypi.org/project/pyproj/.
3. Create a draft PR at https://github.com/conda-forge/pyproj-feedstock and verify tests pass.
4. Verify Debian builds were successful on the release discussion.
5. Verify Fedora builds were successful on the release discussion.
6. Verify the docs build successfully.

## Phase 2: Make the release

After the candidate has proven itself, it will be promoted to a final release.

### Remove the rc postfix

Remove the `rc` postfix from the the version number `__version__` in `__init__.py` (ex. `3.7.2rc0` -> `3.7.2`).

### Create a tag on the repository

The next step is to create a tag with the name `<major>.<minor>.<patch>`. This can be done using the git command line. For example:

```
git tag -a 3.7.2 -m "Version 3.7.2"
```

This creates an annotated git tag meant for releases.

Push the tag to github with:

```bash
git push --follow-tags
```

### Create a GitHub Release

1. Go to https://github.com/pyproj4/pyproj/releases.
2. Click "Draft a new release".
3. Select the release candidate tag you just pushed from the "Select tag" dropdown list.
4. Enter "X.Y.Z" as the Release title using the version number you created.
5. In the description enter "MNT: Version X.Y.Z"
6. Click "Publish release".

Next, go through the history and add release notes (see: [automatically generated release notes](https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes)). Make sure to acknowledge contributions made by others in the release.

### The wheels

The wheels are tested with each merge to main and uploaded to https://pypi.anaconda.org/scientific-python-nightly-wheels/simple in GitHub Actions. They are uploaded to pypi on pre-release and release in GitHub Actions.

### Verify conda-forge build is correct

A PR for `pyproj` will be generated automatically after you push to pypi.
Verify all is correct on the PR at https://github.com/conda-forge/pyproj-feedstock.

### Update the docs

On the `gh-pages` branch, update the stable symlink to point to the next version.
