#!/bin/bash

###################################
# README

# Usage:
# To increment the major version, include [major] in your commit message.
# To increment the minor version, include [minor] in your commit message.
# To increment the patch version, either include [patch] or omit any version keywords in your commit message.

# Example commit messages:
# git commit -m "Add new feature [minor]"
# git commit -m "Fix critical bug [patch]"
# git commit -m "Introduce breaking changes [major]"

###################################

# Configure git
git config user.name "Bitbucket Pipeline"
git config user.email "noreply@bitbucket.org"

# Fetch all tags
git fetch --tags

# Get the latest tag, ignoring tags with '-dev-tested'
LATEST_TAG=$(git tag -l | grep -v '\(dev-tested\|rc\|beta-release\|prod-release\)$' | sort -V | tail -n 1)

# Remove 'v' prefix if it exists
LATEST_TAG=${LATEST_TAG#v}

# Get the latest commit message
COMMIT_MESSAGE=$(git log -1 --pretty=%B)

# Determine which part of the version to increment based on the commit message
if [[ $COMMIT_MESSAGE == *"[major]"* ]]; then
  PART="major"
elif [[ $COMMIT_MESSAGE == *"[minor]"* ]]; then
  PART="minor"
else
  PART="patch"
fi

# Increment the version
IFS='.' read -r -a VERSION_PARTS <<< "$LATEST_TAG"
case $PART in
  major)
    VERSION_PARTS[0]=$((VERSION_PARTS[0] + 1))
    VERSION_PARTS[1]=0
    VERSION_PARTS[2]=0
    ;;
  minor)
    VERSION_PARTS[1]=$((VERSION_PARTS[1] + 1))
    VERSION_PARTS[2]=0
    ;;
  patch)
    VERSION_PARTS[2]=$((VERSION_PARTS[2] + 1))
    ;;
  *)
    echo "Unknown part: $PART"
    exit 1
    ;;
esac

NEW_TAG="v${VERSION_PARTS[0]}.${VERSION_PARTS[1]}.${VERSION_PARTS[2]}"

# Create a new tag
git tag -a $NEW_TAG -m "Bump version to $NEW_TAG [skip ci]"

# Push the new tag
git push origin $NEW_TAG

# Update setup.py with the new version
sed "s/version=\"[^\"]*\"/version=\"${NEW_TAG#v}\"/" setup.py > setup.py.tmp && mv setup.py.tmp setup.py
