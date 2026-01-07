{
  description = "Gmail MCP Server Development Environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = nixpkgs.legacyPackages.${system};
    in {
      devShells.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          git
          alejandra
          (python313.withPackages (ps: with ps; [
            google-auth
            google-auth-oauthlib
            google-api-python-client
            pytest
            pytest-asyncio
            pytest-cov
            ruff
          ]))
          uv
        ];

        shellHook = ''
          export PROJECT_ROOT=$(pwd)
          echo "Gmail MCP development environment loaded"
          echo "Python: $(python --version)"
        '';
      };
    });
}
