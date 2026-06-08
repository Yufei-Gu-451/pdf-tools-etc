# pdf-tools-etc

Personal tools with PDFs and related utilities.

## Local Conda Setup

This project can use a repo-local Conda environment at `./.conda` with a local Miniforge bootstrap at `./.miniforge`.

```sh
ARCH="$(uname -m)"

if [ "$ARCH" = "arm64" ]; then
  INSTALLER_URL="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-arm64.sh"
elif [ "$ARCH" = "x86_64" ]; then
  INSTALLER_URL="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-x86_64.sh"
else
  echo "Unsupported macOS architecture: $ARCH" >&2
  exit 1
fi

curl -L -o "Miniforge3.sh" "$INSTALLER_URL"
bash "Miniforge3.sh" -b -p "$(pwd)/.miniforge"
"$(pwd)/.miniforge/bin/conda" create -y -p "$(pwd)/.conda" python pip
"$(pwd)/.conda/bin/pip" install pymupdf
rm -f "Miniforge3.sh"
```

Activate the environment with:

```sh
source "$(pwd)/.miniforge/bin/activate"
conda activate "$(pwd)/.conda"
```
