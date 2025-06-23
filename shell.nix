{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    pkgs.python3 # Provides the base Python interpreter for Poetry to use
    pkgs.poetry  # Provides the poetry executable
    pkgs.stdenv.cc.cc.lib # Crucial for libstdc++.so.6
    # Add any other system dependencies your project might need
    # e.g., pkgs.sqlite for your database, if it's a native dependency
  ];

  shellHook = ''
    export LD_LIBRARY_PATH=${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH
    echo "Nix shell activated. Python, Poetry, and C++ libraries are available."
    # Auto-activate your poetry environment if it's within the project
    # This assumes your virtualenv is named ".venv" as is common with poetry
    if [ -f .venv/bin/activate ]; then
      source .venv/bin/activate
    fi
  '';
}
