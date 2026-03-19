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

        yt-dlp = pkgs.stdenv.mkDerivation {
          name = "yt-dlp-2026.03.17";
          dontUnpack = true;
          nativeBuildInputs = [ pkgs.autoPatchelfHook ];
          buildInputs = [
            pkgs.zlib
            pkgs.gcc.cc.lib
          ];
          installPhase = ''
            install -Dm755 ${
              pkgs.fetchurl {
                url = "https://github.com/yt-dlp/yt-dlp/releases/download/2026.03.17/yt-dlp_linux";
                hash = "sha256-wrAYn1gf5KLd1BlU8by30yfbBLB+0N6pfk8bPgm13Y4=";
              }
            } $out/bin/yt-dlp
            chmod +x $out/bin/yt-dlp
          '';
        };

        twitch-cli = self.inputs.twitchdownloadercli.packages.${pkgs.system}.twitchdownloadercli;
      in
      {
        packages.default = pkgs.stdenv.mkDerivation {
          pname = "streamorganizer";
          version = "2.0";

          src = ./.;

          nativeBuildInputs = [
            pkgs.makeWrapper
          ];

          buildInputs = [
            pkgs.python3
            pkgs.deno
            yt-dlp
            twitch-cli
          ];

          installPhase = ''
            mkdir -p $out/bin
            mkdir -p $out/lib/python3.12/site-packages

            cp $src/main.py $out/bin/streamorganizer
            cp -r $src/src $out/lib/python3.12/site-packages/
            chmod +x $out/bin/streamorganizer

            wrapProgram $out/bin/streamorganizer \
              --prefix PATH : "${yt-dlp}/bin" \
              --prefix PATH : "${twitch-cli}/bin" \
              --prefix PATH : "${pkgs.deno}/bin
          '';
        };

        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            (python3.withPackages (ps: [ ]))
            deno
            self.inputs.twitchdownloadercli.packages.${pkgs.system}.twitchdownloadercli

            (pkgs.stdenv.mkDerivation {
              name = "yt-dlp-2026.03.17";
              dontUnpack = true;
              nativeBuildInputs = [ pkgs.autoPatchelfHook ];
              buildInputs = [
                pkgs.zlib
                pkgs.gcc.cc.lib
              ];
              installPhase = ''
                install -Dm755 ${
                  pkgs.fetchurl {
                    url = "https://github.com/yt-dlp/yt-dlp/releases/download/2026.03.17/yt-dlp_linux";
                    hash = "sha256-wrAYn1gf5KLd1BlU8by30yfbBLB+0N6pfk8bPgm13Y4=";
                  }
                } $out/bin/yt-dlp
                chmod +x $out/bin/yt-dlp
              '';
            })
          ];
        };
      }
    );
}
