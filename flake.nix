{
  description = "OpenWebUI Extras";

  inputs = {
    nixpkgs.url = "nixpkgs/nixos-24.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        pythonEnv = pkgs.python39.withPackages (ps: with ps; [
          pip
          virtualenv
        ]);
      in
      {
        devShell = pkgs.mkShell {
          buildInputs = with pkgs; [
            # Python
            pythonEnv

            # Development tools
            black
            mypy
            python39Packages.flake8
            python39Packages.pip-tools

            # Build dependencies
            pkg-config
            openssl

            # Development utilities
            direnv
          ];

          shellHook = ''
            # Create and activate virtual environment if it doesn't exist
            if [ ! -d ".venv" ]; then
              ${pythonEnv}/bin/python -m venv .venv
            fi
            source .venv/bin/activate

            # Install development dependencies
            ${pythonEnv}/bin/pip install -r requirements-dev.txt

            # Set environment variables
            export PYTHONPATH="$PWD:$PYTHONPATH"

            echo "Development environment ready!"
          '';
        };
      }
    );
}
