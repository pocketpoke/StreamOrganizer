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
    }@inputs:
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
            pkgs.deno
          ];

          installPhase = ''
            mkdir -p $out/bin

            cp $src/main.py $out/bin/streamorganizer
            chmod +x $out/bin/streamorganizer

            wrapProgram $out/bin/streamorganizer \
              --prefix PATH : ${
                pkgs.lib.makeBinPath [
                  pkgs.deno
                  (pkgs.stdenv.mkDerivation {
                    name = "yt-dlp-2026.03.03";
                    dontUnpack = true;
                    nativeBuildInputs = [ pkgs.autoPatchelfHook ];
                    buildInputs = [
                      pkgs.zlib
                      pkgs.gcc.cc.lib
                    ];
                    installPhase = ''
                      install -Dm755 ${
                        pkgs.fetchurl {
                          url = "https://github.com/yt-dlp/yt-dlp/releases/download/2026.03.03/yt-dlp_linux";
                          hash = "sha256-zHBrlM3hz5LMFV42MqopCrXzgJrajFbCMxEzVQjezfk=";
                        }
                      } $out/bin/yt-dlp
                      chmod +x $out/bin/yt-dlp
                    '';
                  })

                  inputs.twitchdownloadercli.packages.${pkgs.system}.twitchdownloadercli
                ]
              }
          '';
        };

        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            (python3.withPackages (ps: [ ]))
            deno

            (pkgs.stdenv.mkDerivation {
              name = "yt-dlp-2026.03.03";
              dontUnpack = true;
              nativeBuildInputs = [ pkgs.autoPatchelfHook ];
              buildInputs = [
                pkgs.zlib
                pkgs.gcc.cc.lib
              ];
              installPhase = ''
                install -Dm755 ${
                  pkgs.fetchurl {
                    url = "https://github.com/yt-dlp/yt-dlp/releases/download/2026.03.03/yt-dlp_linux";
                    hash = "sha256-zHBrlM3hz5LMFV42MqopCrXzgJrajFbCMxEzVQjezfk=";
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
