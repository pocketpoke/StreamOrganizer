{
  description = "StreamOrganizer - A tool for organizing stream VODs and chats";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
    flake-utils.url = "github:numtide/flake-utils";
    twitchdownloadercli.url = "github:pocketpoke/TwitchDownloaderCLI-Nix-Flake";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      twitchdownloadercli,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        packages.default = pkgs.stdenv.mkDerivation {
          pname = "streamorganizer";
          version = "0.1.1";

          src = ./.;

          nativeBuildInputs = [
            pkgs.makeWrapper
          ];

          buildInputs = [
            pkgs.python3
            pkgs.yt-dlp
            pkgs.deno
            twitchdownloadercli
          ];

          installPhase = ''
            mkdir -p $out/bin

            cp $src/main.py $out/bin/streamorganizer
            chmod +x $out/bin/streamorganizer

            wrapProgram $out/bin/streamorganizer
          '';
        };

        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            (python3.withPackages (ps: [ ]))
            deno
            yt-dlp
            self.inputs.twitchdownloadercli.packages.${pkgs.system}.twitchdownloadercli
          ];
        };
      }
    );
}
