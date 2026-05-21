{
  description = "Develop Python on Nix with uv";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-25.11";
  };

  outputs =
    { nixpkgs, ... }:
    let
      inherit (nixpkgs) lib;
      forAllSystems = lib.genAttrs lib.systems.flakeExposed;
    in
    {
      devShells = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
					dev-script = pkgs.writeShellScriptBin "dev" ''
            python -m watchfiles \
              --ignore-paths __pycache__ \
              "python main.py"
          '';
        in
        {
          default = pkgs.mkShell {
            packages = with pkgs; [
              (pkgs.python3.withPackages (ps: with ps; [
                tkinter
								watchfiles
								ipykernel
              ]))
              ruff
              basedpyright
							dev-script
            ];

          };
        }
      );
    };
}
